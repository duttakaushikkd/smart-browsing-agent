from urllib.parse import urlparse
from config.settings import Settings


class SecurityPolicyError(ValueError):
    """Raised when a requested browser action violates service policy."""


class UrlPolicy:
    """URL allow/block validation with basic SSRF protection."""

    def __init__(self, settings: Settings) -> None:
        self._allowed = set(settings.allowed_domains)
        self._blocked = set(settings.blocked_domains)

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise SecurityPolicyError("Only http and https URLs are allowed")
        host = (parsed.hostname or "").lower()
        if not host:
            raise SecurityPolicyError("URL must include a hostname")
        if host in self._blocked or any(host.endswith(f".{domain}") for domain in self._blocked):
            raise SecurityPolicyError("Target host is blocked")
        if self._allowed and host not in self._allowed and not any(
            host.endswith(f".{domain}") for domain in self._allowed
        ):
            raise SecurityPolicyError("Target host is not in the allow list")
