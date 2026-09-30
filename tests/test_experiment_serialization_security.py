import json

import pytest

from experiments.serialization import SerializationError, canonical_json


BENIGN_IDENTIFIERS = (
    "RuntimeCredential",
    "CredentialStore",
    "TokenParser",
    "ApiKeyValidator",
    "SecretManagerFactory",
    "access_token_parser",
    "password_policy",
)


@pytest.mark.parametrize("identifier", BENIGN_IDENTIFIERS)
def test_benign_source_identifiers_are_data(identifier):
    symbol = "symbol:" + json.dumps(
        {"language": "python", "relative_path": "src/security.py",
         "qualified_name": identifier, "kind": "class",
         "semantic_disambiguator": None, "fallback_line": None},
        sort_keys=True, separators=(",", ":"),
    )
    artifact = {
        "query_id": identifier,
        "retrieval": [{"candidate_identity": symbol,
                       "symbol_id": {"qualified_name": identifier}}],
        "nested": [{"metric_inputs": {symbol: 2, f"file:src/{identifier}.py": 1}}],
    }
    restored = json.loads(canonical_json(artifact))
    assert restored["nested"][0]["metric_inputs"][symbol] == 2


@pytest.mark.parametrize("field", (
    "credential", "password", "api_key", "access_token",
    "authorization", "private_key", "secret",
))
def test_credential_bearing_fields_still_fail_closed(field):
    with pytest.raises(SerializationError, match="credential-bearing field"):
        canonical_json({"nested": [{field: "cleartext-value"}]})


@pytest.mark.parametrize("secret", (
    "sk-proj-abcdefghijklmnop", "Bearer abcdefghijklmnop",
    "Authorization: Bearer abcdefghijklmnop",
    "-----BEGIN PRIVATE KEY-----\nabcdef\n-----END PRIVATE KEY-----",
    "AKIAABCDEFGHIJKLMNOP", "password = hunter2", "password=1",
    "secret: cleartext",
    '"credential": "cleartext"', "SECRET_MARKER", "SOURCE_MARKER",
))
def test_secret_content_is_rejected_in_values_and_candidate_keys(secret):
    with pytest.raises(SerializationError, match="credential-like"):
        canonical_json({"nested": [{"value": secret}]})
    with pytest.raises(SerializationError, match="credential-like"):
        canonical_json({"metric_inputs": {f"file:{secret}": 2}})


def test_mixed_benign_and_secret_object_fails():
    with pytest.raises(SerializationError, match="credential-like"):
        canonical_json({"metric_inputs": {"file:src/RuntimeCredential.py": 2},
                        "retrieved": [{"candidate_identity": "TokenParser"}],
                        "details": ["password_policy", "sk-abcdefghijklmnop"]})


def test_metric_inputs_exception_applies_only_to_relevance_identity_keys():
    with pytest.raises(SerializationError, match="credential-bearing field"):
        canonical_json({"metric_inputs": {"RuntimeCredential": "cleartext-value"}})
    with pytest.raises(SerializationError, match="credential-bearing field"):
        canonical_json({"other_map": {"RuntimeCredential": 2}})
    with pytest.raises(SerializationError, match="credential-bearing field"):
        canonical_json({"metric_inputs": {"api_key": 2}})
    with pytest.raises(SerializationError, match="credential"):
        canonical_json({"metric_inputs": {"symbol:{\"api_key\":\"x\"}": 2}})
