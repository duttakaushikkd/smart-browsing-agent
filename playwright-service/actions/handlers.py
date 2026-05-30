from typing import Any
import structlog
from playwright.async_api import Page, BrowserContext
from schemas.responses import ToolResult
from extractors.dom import extract_compressed_dom

logger = structlog.get_logger(__name__)


def resolve_selector(target_ref: str) -> str:
    if target_ref.startswith("el:"):
        return f'[data-agent-ref="{target_ref}"]'
    return target_ref


async def handle_action(
    action: str,
    payload: dict[str, Any],
    page: Page,
    context: BrowserContext,
) -> ToolResult:
    """Dispatches request payload to corresponding Playwright API handler."""
    logger.info("executing_playwright_action", action=action, payload=payload)
    try:
        match action:
            case "open_url":
                url = payload.get("url")
                if not url:
                    return ToolResult(success=False, error="URL payload argument missing")
                await page.goto(url, wait_until="load")
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "click_element":
                ref = payload.get("target_ref")
                if not ref:
                    return ToolResult(success=False, error="target_ref argument missing")
                selector = resolve_selector(ref)
                await page.click(selector)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "type_text":
                ref = payload.get("target_ref")
                text = payload.get("text", "")
                clear_first = payload.get("clear_first", True)
                if not ref:
                    return ToolResult(success=False, error="target_ref argument missing")
                selector = resolve_selector(ref)
                if clear_first:
                    await page.fill(selector, "")
                await page.type(selector, text)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "extract_text":
                ref = payload.get("target_ref")
                if ref:
                    selector = resolve_selector(ref)
                    text = await page.inner_text(selector)
                else:
                    text = await page.evaluate("() => document.body.innerText")
                return ToolResult(success=True, data={"text": text})

            case "screenshot":
                full_page = payload.get("full_page", False)
                # Store as base64 representation to return easily via JSON
                screenshot_bytes = await page.screenshot(full_page=full_page)
                import base64
                encoded = base64.b64encode(screenshot_bytes).decode("utf-8")
                return ToolResult(
                    success=True,
                    data={"screenshot": encoded},
                    metadata={"format": "base64", "mime_type": "image/png"},
                )

            case "get_dom_snapshot":
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "wait_for_element":
                ref = payload.get("target_ref")
                timeout = payload.get("timeout_ms", 5000)
                if not ref:
                    return ToolResult(success=False, error="target_ref argument missing")
                selector = resolve_selector(ref)
                await page.wait_for_selector(selector, timeout=timeout)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "scroll_page":
                direction = payload.get("direction", "down")
                amount = payload.get("amount_px", 800)
                scroll_value = amount if direction == "down" else -amount
                await page.evaluate(f"window.scrollBy(0, {scroll_value})")
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "go_back":
                await page.go_back()
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "hover_element":
                ref = payload.get("target_ref")
                if not ref:
                    return ToolResult(success=False, error="target_ref argument missing")
                selector = resolve_selector(ref)
                await page.hover(selector)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "press_key":
                key = payload.get("key")
                if not key:
                    return ToolResult(success=False, error="key argument missing")
                ref = payload.get("target_ref")
                if ref:
                    selector = resolve_selector(ref)
                    await page.focus(selector)
                await page.keyboard.press(key)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "select_dropdown":
                ref = payload.get("target_ref")
                value = payload.get("value")
                label = payload.get("label")
                if not ref:
                    return ToolResult(success=False, error="target_ref argument missing")
                selector = resolve_selector(ref)
                if value:
                    await page.select_option(selector, value=value)
                elif label:
                    await page.select_option(selector, label=label)
                else:
                    return ToolResult(success=False, error="either value or label must be provided")
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "upload_file":
                ref = payload.get("target_ref")
                file_path = payload.get("file_path")
                if not ref or not file_path:
                    return ToolResult(success=False, error="target_ref and file_path are required")
                selector = resolve_selector(ref)
                await page.set_input_files(selector, file_path)
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "switch_tab":
                tab_id = payload.get("tab_id")
                if not tab_id:
                    return ToolResult(success=False, error="tab_id argument missing")
                # Switches context focus (Playwright doesn't require active tab toggle for APIs, but we trace it)
                return ToolResult(success=True, data={"switched_to": tab_id})

            case "close_tab":
                # Close the active page context
                await page.close()
                return ToolResult(success=True, data={"closed": True})

            case "refresh_page":
                await page.reload()
                dom = await extract_compressed_dom(page)
                return ToolResult(success=True, data=dom)

            case "extract_links":
                max_links = payload.get("max_links", 100)
                links = await page.evaluate(
                    """
                    (max) => {
                        return Array.from(document.querySelectorAll('a'))
                            .map(a => ({ text: a.innerText.trim(), url: a.href }))
                            .filter(link => link.url && link.url.startsWith('http'))
                            .slice(0, max);
                    }
                    """,
                    max_links,
                )
                return ToolResult(success=True, data={"links": links})

            case "extract_tables":
                tables = await page.evaluate(
                    """
                    () => {
                        return Array.from(document.querySelectorAll('table')).map(table => {
                            const rows = Array.from(table.querySelectorAll('tr'));
                            return rows.map(row => Array.from(row.querySelectorAll('td, th')).map(cell => cell.innerText.trim()));
                        });
                    }
                    """
                )
                return ToolResult(success=True, data={"tables": tables})

            case "execute_javascript":
                script = payload.get("script")
                if not script:
                    return ToolResult(success=False, error="script argument missing")
                result = await page.evaluate(script)
                return ToolResult(success=True, data={"result": result})

            case _:
                return ToolResult(success=False, error=f"Unknown browser action: {action}")

    except Exception as exc:
        logger.exception("action_failed", action=action, error=str(exc))
        return ToolResult(success=False, error=str(exc))
