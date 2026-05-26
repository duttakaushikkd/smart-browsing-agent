import pytest

from config.settings import Settings
from security.url_policy import SecurityPolicyError, UrlPolicy


def test_url_policy_blocks_private_hosts() -> None:
    policy = UrlPolicy(Settings(blocked_domains=["127.0.0.1"], allowed_domains=[]))

    with pytest.raises(SecurityPolicyError):
        policy.validate_url("http://127.0.0.1:9000/admin")


def test_url_policy_allows_configured_domain() -> None:
    policy = UrlPolicy(Settings(allowed_domains=["example.com"], blocked_domains=[]))

    policy.validate_url("https://shop.example.com/search")


def test_url_policy_rejects_unlisted_domain() -> None:
    policy = UrlPolicy(Settings(allowed_domains=["example.com"], blocked_domains=[]))

    with pytest.raises(SecurityPolicyError):
        policy.validate_url("https://evil.test")
