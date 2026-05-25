from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.core.security import UrlPolicy
from app.schemas.tools import (
    ClickElementArgs,
    DomSnapshotArgs,
    ExtractTextArgs,
    GoBackArgs,
    OpenUrlArgs,
    ScreenshotArgs,
    ScrollPageArgs,
    ToolResult,
    TypeTextArgs,
    WaitForElementArgs,
)
from app.services.browser_client import BrowserServiceClient


class ToolExecutionContext(BaseModel):
    session_id: str


class Tool[ArgsT: BaseModel](ABC):
    name: str
    description: str
    args_model: type[ArgsT]

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_model.model_json_schema(),
            },
        }

    def validate_args(self, arguments: dict[str, Any]) -> ArgsT:
        return self.args_model.model_validate(arguments)

    @abstractmethod
    async def execute(self, context: ToolExecutionContext, arguments: ArgsT) -> ToolResult:
        """Execute the abstract tool through the external browser service API."""


class BrowserApiTool[ArgsT: BaseModel](Tool[ArgsT]):
    """Planner-visible abstract tool backed only by external browser service APIs."""

    def __init__(self, client: BrowserServiceClient) -> None:
        self._client = client

    async def _call_browser(self, context: ToolExecutionContext, arguments: ArgsT) -> ToolResult:
        return await self._client.execute_action(
            session_id=context.session_id,
            action=self.name,
            payload=arguments.model_dump(exclude_none=True),
        )


class OpenUrlTool(BrowserApiTool[OpenUrlArgs]):
    name = "open_url"
    description = "Open an HTTP or HTTPS URL in the isolated browser session."
    args_model = OpenUrlArgs

    def __init__(self, client: BrowserServiceClient, url_policy: UrlPolicy) -> None:
        super().__init__(client)
        self._url_policy = url_policy

    async def execute(self, context: ToolExecutionContext, arguments: OpenUrlArgs) -> ToolResult:
        self._url_policy.validate_url(arguments.url)
        return await self._call_browser(context, arguments)


class ClickElementTool(BrowserApiTool[ClickElementArgs]):
    name = "click_element"
    description = "Click an actionable UI element using an opaque target reference."
    args_model = ClickElementArgs

    async def execute(
        self, context: ToolExecutionContext, arguments: ClickElementArgs
    ) -> ToolResult:
        return await self._call_browser(context, arguments)


class TypeTextTool(BrowserApiTool[TypeTextArgs]):
    name = "type_text"
    description = "Type text into an input-like UI element using an opaque target reference."
    args_model = TypeTextArgs

    async def execute(self, context: ToolExecutionContext, arguments: TypeTextArgs) -> ToolResult:
        return await self._call_browser(context, arguments)


class ExtractTextTool(BrowserApiTool[ExtractTextArgs]):
    name = "extract_text"
    description = "Extract visible text from the page or an observed semantic region."
    args_model = ExtractTextArgs

    async def execute(
        self, context: ToolExecutionContext, arguments: ExtractTextArgs
    ) -> ToolResult:
        return await self._call_browser(context, arguments)


class ScreenshotTool(BrowserApiTool[ScreenshotArgs]):
    name = "screenshot"
    description = "Request a screenshot artifact from the external browser service."
    args_model = ScreenshotArgs

    async def execute(self, context: ToolExecutionContext, arguments: ScreenshotArgs) -> ToolResult:
        return await self._call_browser(context, arguments)


class WaitForElementTool(BrowserApiTool[WaitForElementArgs]):
    name = "wait_for_element"
    description = "Wait for an observed semantic element reference to become available."
    args_model = WaitForElementArgs

    async def execute(
        self, context: ToolExecutionContext, arguments: WaitForElementArgs
    ) -> ToolResult:
        return await self._call_browser(context, arguments)


class GetDomSnapshotTool(BrowserApiTool[DomSnapshotArgs]):
    name = "get_dom_snapshot"
    description = "Get compressed visible semantic elements, not full raw HTML."
    args_model = DomSnapshotArgs

    async def execute(
        self, context: ToolExecutionContext, arguments: DomSnapshotArgs
    ) -> ToolResult:
        return await self._call_browser(context, arguments)


class ScrollPageTool(BrowserApiTool[ScrollPageArgs]):
    name = "scroll_page"
    description = "Scroll the active page by direction and bounded amount."
    args_model = ScrollPageArgs

    async def execute(self, context: ToolExecutionContext, arguments: ScrollPageArgs) -> ToolResult:
        return await self._call_browser(context, arguments)


class GoBackTool(BrowserApiTool[GoBackArgs]):
    name = "go_back"
    description = "Navigate back in browser history for the active tab."
    args_model = GoBackArgs

    async def execute(self, context: ToolExecutionContext, arguments: GoBackArgs) -> ToolResult:
        return await self._call_browser(context, arguments)


class ToolNotFoundError(KeyError):
    """Raised when the planner asks for an unregistered tool."""


class ToolRegistry:
    """Registry that owns schema exposure, validation, and tool dispatch."""

    def __init__(self, tools: list[Tool[Any]]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def openai_schemas(self) -> list[dict[str, Any]]:
        return [tool.openai_schema() for tool in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        validated = tool.validate_args(arguments)
        return await tool.execute(context, validated)

    def names(self) -> list[str]:
        return list(self._tools)


def create_browser_api_tools(
    client: BrowserServiceClient,
    url_policy: UrlPolicy,
) -> list[Tool[Any]]:
    return [
        OpenUrlTool(client, url_policy),
        ClickElementTool(client),
        TypeTextTool(client),
        ExtractTextTool(client),
        ScreenshotTool(client),
        WaitForElementTool(client),
        GetDomSnapshotTool(client),
        ScrollPageTool(client),
        GoBackTool(client),
    ]
