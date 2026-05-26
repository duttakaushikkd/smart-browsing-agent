class McpClientError(RuntimeError):
    """Base exception for MCP client failures."""


class McpTransportError(McpClientError):
    """HTTP transport failure talking to MCP server."""


class McpToolNotFoundError(McpClientError):
    """Requested tool is not exposed by MCP server."""


class McpResponseError(McpClientError):
    """MCP server returned an invalid response payload."""
