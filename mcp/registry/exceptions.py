class ToolLayerError(RuntimeError):
    """Base exception for MCP tool layer failures."""


class ToolExecutionError(ToolLayerError):
    """Tool ran but failed or returned an error envelope."""


class ToolTimeoutError(ToolLayerError):
    """Tool execution exceeded the configured deadline."""


class ToolValidationError(ToolLayerError):
    """Incoming arguments failed schema or policy validation."""


class ToolUnavailableError(ToolLayerError):
    """Tool is not registered or not permitted for this session."""


class BrowserServiceError(ToolLayerError):
    """The browser execution service rejected the call or returned an invalid body."""


class ToolRegistryConflictError(ToolLayerError):
    """Duplicate tool name registration."""


class CircuitOpenError(ToolLayerError):
    """Circuit breaker prevented the outbound browser call."""
