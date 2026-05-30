import pytest
from unittest.mock import AsyncMock, MagicMock
from security.url_policy import UrlPolicy, SecurityPolicyError
from config.settings import Settings
from actions.handlers import resolve_selector, handle_action
from schemas.responses import ToolResult


def test_url_policy() -> None:
    settings = Settings(allowed_domains=[], blocked_domains=["localhost", "127.0.0.1"])
    policy = UrlPolicy(settings)

    # Valid URLs
    policy.validate_url("https://google.com")
    policy.validate_url("https://amazon.co.uk")

    # Invalid Schemes
    with pytest.raises(SecurityPolicyError, match="Only http and https URLs are allowed"):
        policy.validate_url("ftp://google.com")

    # Blocked Domains
    with pytest.raises(SecurityPolicyError, match="Target host is blocked"):
        policy.validate_url("https://localhost")
    with pytest.raises(SecurityPolicyError, match="Target host is blocked"):
        policy.validate_url("https://sub.127.0.0.1")


def test_resolve_selector() -> None:
    assert resolve_selector("el:1") == '[data-agent-ref="el:1"]'
    assert resolve_selector("#my-id") == "#my-id"


@pytest.mark.asyncio
async def test_handle_action_unknown() -> None:
    page = AsyncMock()
    context = MagicMock()
    result = await handle_action("invalid_action", {}, page, context)
    assert result.success is False
    assert "Unknown browser action" in result.error
