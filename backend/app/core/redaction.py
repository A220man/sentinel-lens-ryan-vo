"""Secret and credential redaction pipeline for step traces and session artifacts."""

import re
from typing import Any, Dict, List, Set, Union


# Sensitive keys whose values should always be scrubbed
SENSITIVE_KEY_NAMES: Set[str] = {
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "client_secret",
    "private_key",
    "session_secret",
    "cookie",
    "set-cookie",
}

# Regex patterns for common sensitive token formats in raw text
AUTH_HEADER_PATTERN = re.compile(
    r"(?i)(authorization|proxy-authorization)\s*:\s*(bearer|basic)\s+[^\s,]+", re.IGNORECASE
)
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]{12,}\b")
BASIC_PATTERN = re.compile(r"(?i)\bbasic\s+[a-zA-Z0-9\+/=]{16,}\b")
# Generic secret pattern: capture the key name in group 1, value in group 2
GENERIC_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{16,})['\"]?"
)
JWT_PATTERN = re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b")


class RedactionFilter:
    """Recursively scrubs secrets and credential patterns from session data and logs."""

    def __init__(self, additional_sensitive_keys: Union[List[str], Set[str], None] = None):
        self.sensitive_keys = set(SENSITIVE_KEY_NAMES)
        if additional_sensitive_keys:
            self.sensitive_keys.update(k.lower() for k in additional_sensitive_keys)

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name exactly matches or is a known sensitive prefix."""
        lower_key = key.lower()
        # Exact match or known prefixes that indicate sensitivity
        for sensitive in self.sensitive_keys:
            if lower_key == sensitive or lower_key.startswith(sensitive + "_") or lower_key.endswith("_" + sensitive):
                return True
        return False

    def redact_text(self, text: str) -> str:
        """Applies regex scrubbers to raw string content."""
        if not text or not isinstance(text, str):
            return text

        result = text
        # Auth header pattern runs first to catch "Authorization: Bearer <token>"
        result = AUTH_HEADER_PATTERN.sub(r"\1: \2 [REDACTED_CREDENTIAL]", result)
        # Bearer pattern should not match already redacted tokens
        result = BEARER_PATTERN.sub("Bearer [REDACTED_CREDENTIAL]", result)
        result = BASIC_PATTERN.sub("Basic [REDACTED_AUTH]", result)
        # Generic secret pattern: capture the key name and replace value
        result = GENERIC_SECRET_PATTERN.sub(r"\1=[REDACTED_KEY]", result)
        result = JWT_PATTERN.sub("[REDACTED_JWT_TOKEN]", result)
        return result

    def redact_data(self, data: Any) -> Any:
        """Recursively traverses dictionaries, lists, and scalars to scrub secrets."""
        if isinstance(data, dict):
            scrubbed: Dict[str, Any] = {}
            for key, val in data.items():
                if self._is_sensitive_key(str(key)):
                    scrubbed[key] = "[REDACTED_CREDENTIAL]"
                else:
                    scrubbed[key] = self.redact_data(val)
            return scrubbed
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self.redact_data(item) for item in data)
        elif isinstance(data, str):
            return self.redact_text(data)
        return data


default_redactor = RedactionFilter()
