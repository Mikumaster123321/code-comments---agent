import sys

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
