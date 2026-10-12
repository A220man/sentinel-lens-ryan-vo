"""Tests for secret redaction pipeline and credential scrubbing."""

from app.core.redaction import RedactionFilter


def test_redact_sensitive_keys_in_dictionary():
    redactor = RedactionFilter()
    synthetic_key_value = "dyn-secret-" + ("0" * 24)
    data = {
        "username": "developer_test",
        "api_key": synthetic_key_value,
        "token": "tok-" + ("a" * 16),
        "nested": {
            "password": "mypassword123",
            "normal_field": "public_value",
        },
        "list_items": [
            {"access_token": "acc-" + ("9" * 16)},
            {"visible": True},
        ],
    }

    scrubbed = redactor.redact_data(data)
    assert scrubbed["username"] == "developer_test"
    assert scrubbed["api_key"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["token"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["nested"]["password"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["nested"]["normal_field"] == "public_value"
    assert scrubbed["list_items"][0]["access_token"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["list_items"][1]["visible"] is True


def test_redact_authorization_headers_in_text():
    redactor = RedactionFilter()
    synthetic_bearer_token = "tok-" + ("b" * 24)
    raw_log = f"Request headers: Authorization: Bearer {synthetic_bearer_token}, Content-Type: application/json"
    cleaned = redactor.redact_text(raw_log)
    assert synthetic_bearer_token not in cleaned
    assert "Bearer [REDACTED_CREDENTIAL]" in cleaned


def test_redact_jwt_pattern_in_text():
    redactor = RedactionFilter()
    # Construct a synthetic JWT shape at runtime
    synthetic_jwt = "eyJ" + ("1" * 12) + ".eyJ" + ("2" * 12) + "." + ("3" * 12)
    raw_message = f"Session received token: {synthetic_jwt} from callback"
    cleaned = redactor.redact_text(raw_message)
    assert synthetic_jwt not in cleaned
    assert "[REDACTED_JWT_TOKEN]" in cleaned
