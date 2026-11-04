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


def test_redact_bearer_token_idempotent():
    """Redacting already redacted text should not change the output."""
    redactor = RedactionFilter()
    raw = "Authorization: Bearer secrettoken123456"
    first_pass = redactor.redact_text(raw)
    second_pass = redactor.redact_text(first_pass)
    assert first_pass == second_pass
    assert "[REDACTED_CREDENTIAL]" in first_pass


def test_redact_generic_secret_patterns():
    """Test generic secret pattern matching in raw text."""
    redactor = RedactionFilter()
    
    # api_key=value
    raw = "config: api_key=mysecretapikey123456789"
    cleaned = redactor.redact_text(raw)
    assert "mysecretapikey123456789" not in cleaned
    assert "api_key=[REDACTED_KEY]" in cleaned or "api_key = [REDACTED_KEY]" in cleaned
    
    # secret_key: "value"
    raw = 'secret_key: "supersecretvalue123456789"'
    cleaned = redactor.redact_text(raw)
    assert "supersecretvalue123456789" not in cleaned
    assert "[REDACTED_KEY]" in cleaned
    
    # access_token='value'
    raw = "access_token='accesstokenvalue123456789'"
    cleaned = redactor.redact_text(raw)
    assert "accesstokenvalue123456789" not in cleaned
    assert "[REDACTED_KEY]" in cleaned


def test_sensitive_key_matching_precision():
    """Key matching should use exact/prefix/suffix boundaries, not substring."""
    redactor = RedactionFilter()
    data = {
        # These should be redacted (exact match or known prefixes/suffixes)
        "user_auth": "secret123",
        "authorization_code": "auth123",
        "password_hash": "hash123",
        "has_password": "true",
        "token": "tok123",
        "my_token_value": "val123",
        # These should NOT be redacted (substring match only)
        "author_name": "John Doe",
        "authenticated_user": "jane",
        "passwordless_login": True,
        "tokenize_data": "some data",
        "authenticity_token": "real token here",
        "authorization": "Bearer token",
    }
    
    scrubbed = redactor.redact_data(data)
    
    # Should be redacted
    assert scrubbed["user_auth"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["authorization_code"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["password_hash"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["has_password"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["token"] == "[REDACTED_CREDENTIAL]"
    assert scrubbed["my_token_value"] == "[REDACTED_CREDENTIAL]"
    
    # Should NOT be redacted (substring only)
    assert scrubbed["author_name"] == "John Doe"
    assert scrubbed["authenticated_user"] == "jane"
    assert scrubbed["passwordless_login"] is True
    assert scrubbed["tokenize_data"] == "some data"
    assert scrubbed["authenticity_token"] == "real token here"
    assert scrubbed["authorization"] == "[REDACTED_CREDENTIAL]"  # exact match


def test_redact_basic_auth_pattern():
    """Test Basic auth header redaction."""
    redactor = RedactionFilter()
    # Basic auth uses base64 encoded credentials
    import base64
    creds = base64.b64encode(b"user:password12345678901234").decode()
    raw = f"Authorization: Basic {creds}"
    cleaned = redactor.redact_text(raw)
    assert creds not in cleaned
    assert "Basic [REDACTED_AUTH]" in cleaned


def test_redact_proxy_authorization_header():
    """Test Proxy-Authorization header redaction."""
    redactor = RedactionFilter()
    raw = "Proxy-Authorization: Bearer proxytok123456789012"
    cleaned = redactor.redact_text(raw)
    assert "proxytok123456789012" not in cleaned
    assert "Bearer [REDACTED_CREDENTIAL]" in cleaned
