import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from code_maintenance import SymbolId, SymbolKind
from project_intelligence import (
    BM25Config,
    BM25Index,
    DuplicateLexicalDocumentError,
    InvalidBM25ConfigError,
    InvalidLexicalQueryError,
    LexicalHit,
    RetrievalDocument,
    tokenize,
)


def document(name, source, *, path="main.py", kind=SymbolKind.FUNCTION):
    symbol_id = SymbolId("python", path, name, kind)
    return RetrievalDocument(
        symbol_id=symbol_id,
        language="python",
        relative_path=path,
        qualified_name=name,
        kind=kind,
        signature=f"{name}()",
        source_text=source,
        documentation_text=None,
        content_hash="a" * 64,
        start_line=1,
        end_line=max(1, source.count("\n") + 1),
    )


def test_tokenizer_contract_covers_code_identifiers_and_unicode():
    assert tokenize("simpleWord") == ("simpleword", "simple", "word")
    assert tokenize("credit_account") == ("credit_account", "credit", "account")
    assert tokenize("ManagedAccessService") == (
        "managedaccessservice",
        "managed",
        "access",
        "service",
    )
    assert "http" in tokenize("HTTPServer")
    assert "server" in tokenize("HTTPServer")
    assert set(("parse2json", "parse", "2", "json")).issubset(tokenize("parse2JSON"))
    assert set(("qualified", "name")).issubset(tokenize("qualified.name"))
    assert "你好世界" in tokenize("你好世界")
    assert "return" in tokenize('def greet(name):\n    # return hello\n    return "hello"')


def test_config_validation_and_immutable_results():
    assert BM25Config().k1 == 1.5
    assert BM25Config().b == 0.75
    for field, value in (("k1", 0), ("k1", -1), ("b", -0.1), ("b", 1.1), ("k1", math.inf), ("b", math.nan)):
        with pytest.raises(InvalidBM25ConfigError):
            BM25Config(**{field: value})
    with pytest.raises(InvalidBM25ConfigError):
        BM25Config(k1=True)
    hit = BM25Index((document("run", "run run"),)).search("run")[0]
    assert isinstance(hit, LexicalHit)
    with pytest.raises(FrozenInstanceError):
        hit.rank = 2


def test_empty_unknown_and_top_k_queries():
    index = BM25Index((document("run", "run"),))
    assert BM25Index().search("run") == ()
    assert index.search("") == ()
    assert index.search("   ") == ()
    assert index.search("unknown") == ()
    assert len(index.search("run", top_k=10)) == 1
    for value in (True, 0, -1, 1.0, "1"):
        with pytest.raises(InvalidLexicalQueryError):
            index.search("run", value)


def test_duplicate_symbol_ids_fail_closed():
    doc = document("run", "run")
    with pytest.raises(DuplicateLexicalDocumentError):
        BM25Index((doc, doc))


def test_hand_calculation_matches_independent_bm25_oracle():
    docs = (
        document("a", "rare common"),
        document("b", "common common"),
        document("c", "other"),
    )
    index = BM25Index(docs)
    # Each document receives its qualified name plus source text.  For query
    # 'rare', df=1, tf=1 in document a, dl=3, avgdl=8/3.
    n, df, tf, dl, avgdl, k1, b = 3, 1, 1, 3, 8 / 3, 1.5, 0.75
    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
    expected = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    hit = index.search("rare")[0]
    assert hit.document.qualified_name == "a"
    assert hit.score == expected


def test_idf_length_and_tf_saturation():
    docs = (
        document("rare", "rare"),
        document("common1", "common"),
        document("common2", "common"),
    )
    index = BM25Index(docs)
    assert index.document_frequencies["rare"] == 1
    assert index.document_frequencies["common"] == 2
    # Rare terms have higher IDF, and a short matching document beats a padded one.
    assert index.search("rare")[0].score > index.search("common")[0].score

    scores = []
    for count in (1, 2, 10, 100):
        scores.append(BM25Index((document(f"d{count}", " ".join(["term"] * count)),)).search("term")[0].score)
    assert scores[0] < scores[1] < scores[2] < scores[3]
    assert scores[0] / 1 > scores[1] / 2 > scores[2] / 10 > scores[3] / 100


def test_multi_term_determinism_ties_and_input_order_independence():
    docs = (
        document("zeta", "credit ledger"),
        document("alpha", "credit ledger"),
        document("other", "managed access"),
    )
    first = BM25Index(docs).search("CreditLedger")
    second = BM25Index(tuple(reversed(docs))).search("credit ledger")
    assert [(hit.symbol_id, hit.rank, hit.score) for hit in first] == [
        (hit.symbol_id, hit.rank, hit.score) for hit in second
    ]
    assert [hit.document.qualified_name for hit in first] == ["alpha", "zeta"]
    assert [hit.rank for hit in first] == [1, 2]
    assert all(BM25Index(docs).search("credit ledger") == first for _ in range(100))


def test_index_exposes_read_only_metadata_and_does_not_touch_filesystem(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: calls.append(args))
    docs = (document("run", "run"),)
    index = BM25Index(docs)
    assert index.documents == docs
    assert index.document_lengths == (2,)
    assert index.search("run")
    assert calls == []
    with pytest.raises(TypeError):
        index.document_frequencies["run"] = 9
