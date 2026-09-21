import sys
import types
from types import SimpleNamespace

import pytest

from project_intelligence import (
    EmbeddingDependencyError,
    EmbeddingTokenizationError,
    LocalE5EmbeddingProvider,
    MAX_INPUT_POLICY,
    PRIMARY_MODEL_DIMENSION,
    PRIMARY_MODEL_REPOSITORY,
    PRIMARY_MODEL_REVISION,
)


def test_local_adapter_is_lazy_and_has_frozen_primary_fingerprint():
    provider = LocalE5EmbeddingProvider()

    assert provider.loaded is False
    assert provider.fingerprint.runtime_kind == "transformers-torch"
    assert provider.fingerprint.model_repository == PRIMARY_MODEL_REPOSITORY
    assert provider.fingerprint.revision == PRIMARY_MODEL_REVISION
    assert provider.fingerprint.dimension == PRIMARY_MODEL_DIMENSION
    assert provider.fingerprint.max_input_policy == MAX_INPUT_POLICY
    assert provider.fingerprint.query_instruction == "query: "
    assert provider.fingerprint.document_instruction == "passage: "


def test_importing_core_does_not_import_optional_runtime():
    # The adapter module itself only imports standard-library modules plus
    # frozen core contracts; optional names are resolved inside ``load``.
    import project_intelligence.local_embedding as local_embedding

    assert "torch" not in local_embedding.__dict__
    assert "transformers" not in local_embedding.__dict__


def test_missing_optional_runtime_is_a_stable_error(monkeypatch):
    provider = LocalE5EmbeddingProvider()
    monkeypatch.setitem(sys.modules, "torch", None)
    monkeypatch.setitem(sys.modules, "transformers", None)
    with pytest.raises(EmbeddingDependencyError, match="optional local embedding runtime"):
        provider.embed_query("credit ledger")

    assert "blocked for contract test" not in provider.fingerprint.model_repository


def test_explicit_revision_changes_semantic_identity_without_loading_runtime():
    provider = LocalE5EmbeddingProvider(revision="other-fixed-revision")

    assert provider.fingerprint.revision == "other-fixed-revision"
    assert provider.fingerprint.fingerprint_hash != LocalE5EmbeddingProvider().fingerprint.fingerprint_hash


def test_instruction_is_applied_at_most_once():
    provider = LocalE5EmbeddingProvider()

    assert provider._prepare_text("credit ledger", "query") == "query: credit ledger"
    assert provider._prepare_text("query: credit ledger", "query") == "query: credit ledger"
    assert provider._prepare_text("CreditLedger", "document") == "passage: CreditLedger"
    assert provider._prepare_text("passage: CreditLedger", "document") == "passage: CreditLedger"


def test_empty_and_whitespace_inputs_are_rejected_before_model_use():
    provider = LocalE5EmbeddingProvider()

    with pytest.raises(EmbeddingTokenizationError, match="must not"):
        provider.embed_query("")
    with pytest.raises(EmbeddingTokenizationError, match="must not contain"):
        provider.embed_documents(("  ",))


class _DiagnosticEncoding:
    def __init__(self, size):
        self.ids = list(range(size))


class _StatefulDiagnosticBackend:
    def __init__(self):
        self.truncation = None

    def no_truncation(self):
        self.truncation = None

    def enable_truncation(self, **config):
        self.truncation = dict(config)

    def encode(self, text, *, add_special_tokens):
        size = 2004 if add_special_tokens else 2002
        if self.truncation is not None:
            size = min(size, self.truncation["max_length"])
        return _DiagnosticEncoding(size)


def test_diagnose_is_independent_of_inference_mutated_backend_state():
    provider = LocalE5EmbeddingProvider()
    backend = _StatefulDiagnosticBackend()
    provider._tokenizer = SimpleNamespace(backend_tokenizer=backend)
    provider._model = object()

    long_text = "long text"
    before = provider.diagnose(long_text)
    assert before.total_token_count == 2004
    assert before.truncated is True

    # Simulate the shared backend state left by the real tokenizer's inference
    # call. diagnose() must temporarily disable it and restore it afterwards.
    backend.enable_truncation(max_length=512, stride=0, strategy="longest_first", direction="right")
    after = provider.diagnose(long_text)

    assert after == before
    assert backend.truncation["max_length"] == 512


def test_embed_documents_empty_tuple_resets_diagnostics_deterministically():
    provider = LocalE5EmbeddingProvider()

    assert provider.embed_documents(()) == ()
    assert provider.last_diagnostics == ()


class _FakeLoadTokenizer:
    model_max_length = 512


class _FakeLoadModel:
    def __init__(self, *, revision, dimension):
        self.config = SimpleNamespace(_commit_hash=revision, hidden_size=dimension)

    def to(self, _device):
        return self

    def eval(self):
        return self


def _install_fake_runtime(monkeypatch, *, resolved_revision, dimension):
    fake_torch = types.ModuleType("torch")
    fake_torch.device = lambda name: SimpleNamespace(type=name)
    fake_torch.backends = SimpleNamespace(
        mps=SimpleNamespace(is_available=lambda: False)
    )
    fake_transformers = types.ModuleType("transformers")
    fake_transformers.AutoTokenizer = SimpleNamespace(
        from_pretrained=lambda *args, **kwargs: _FakeLoadTokenizer()
    )
    fake_transformers.AutoModel = SimpleNamespace(
        from_pretrained=lambda *args, **kwargs: _FakeLoadModel(
            revision=resolved_revision, dimension=dimension
        )
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)


def test_wrong_resolved_revision_fails_closed(monkeypatch):
    provider = LocalE5EmbeddingProvider()
    _install_fake_runtime(monkeypatch, resolved_revision="wrong", dimension=768)

    from project_intelligence import EmbeddingModelLoadError

    with pytest.raises(EmbeddingModelLoadError, match="unable to load pinned"):
        provider.load()


def test_wrong_model_dimension_fails_closed(monkeypatch):
    provider = LocalE5EmbeddingProvider()
    _install_fake_runtime(monkeypatch, resolved_revision=PRIMARY_MODEL_REVISION, dimension=7)

    from project_intelligence import EmbeddingModelLoadError

    with pytest.raises(EmbeddingModelLoadError, match="unable to load pinned"):
        provider.load()
