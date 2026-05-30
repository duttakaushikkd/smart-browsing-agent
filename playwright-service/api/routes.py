import urllib.parse
from fastapi import APIRouter, Depends, Request, HTTPException
import structlog
from schemas.requests import BrowserActionRequest, BrowserSearchRequest, BrowserExtractRequest
from schemas.responses import (
    SessionCreateResponse,
    SessionCloseRequest,
    SessionCloseResponse,
    SessionStatusResponse,
    ToolResult,
)
from actions.handlers import handle_action
from security.url_policy import UrlPolicy, SecurityPolicyError
from extractors.dom import extract_compressed_dom

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/browser", tags=["browser"])


def get_manager(request: Request):
    return request.app.state.session_manager


def get_policy(request: Request) -> UrlPolicy:
    return request.app.state.url_policy


@router.post("/session/create", response_model=SessionCreateResponse)
async def create_session(request: Request, manager=Depends(get_manager)):
    import uuid
    session_id = str(uuid.uuid4())
    await manager.create_session(session_id)
    return SessionCreateResponse(session_id=session_id)


@router.post("/session/close", response_model=SessionCloseResponse)
async def close_session(payload: SessionCloseRequest, manager=Depends(get_manager)):
    success = await manager.close_session(payload.session_id)
    return SessionCloseResponse(success=success)


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def session_status(session_id: str, manager=Depends(get_manager)):
    session = manager._sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    tabs = [page.url for page in session.context.pages]
    return SessionStatusResponse(session_id=session_id, status="active", tabs=tabs)


@router.post("/action", response_model=ToolResult)
async def execute_action(
    payload: BrowserActionRequest,
    manager=Depends(get_manager),
    policy: UrlPolicy = Depends(get_policy),
):
    session = await manager.get_session(payload.session_id)
    page = await session.get_active_page()

    if payload.action == "open_url":
        url = payload.payload.get("url", "")
        try:
            policy.validate_url(url)
        except SecurityPolicyError as exc:
            return ToolResult(success=False, error=str(exc))

    result = await handle_action(
        action=payload.action,
        payload=payload.payload,
        page=page,
        context=session.context,
    )
    return result


@router.post("/search")
async def execute_search(
    payload: BrowserSearchRequest,
    manager=Depends(get_manager),
):
    session = await manager.get_session(payload.session_id)
    page = await session.get_active_page()

    # Search via DuckDuckGo HTML version
    quoted_query = urllib.parse.quote_plus(payload.query)
    search_url = f"https://html.duckduckgo.com/html/?q={quoted_query}"

    try:
        await page.goto(search_url, wait_until="load")
        results = await page.evaluate(
            """
            () => {
                return Array.from(document.querySelectorAll('.result__body')).map(el => {
                    const a = el.querySelector('.result__title a');
                    const snippet = el.querySelector('.result__snippet');
                    return {
                        title: a ? a.innerText.trim() : '',
                        url: a ? a.href : '',
                        description: snippet ? snippet.innerText.trim() : ''
                    };
                }).filter(r => r.title && r.url);
            }
            """
        )
        observation = await extract_compressed_dom(page)
        return {
            "success": True,
            "results": results[:10],
            "observation": observation,
        }
    except Exception as exc:
        logger.exception("search_action_failed", query=payload.query, error=str(exc))
        return {
            "success": False,
            "results": [],
            "observation": {},
            "error": str(exc),
        }


@router.post("/extract")
async def execute_extract(
    payload: BrowserExtractRequest,
    manager=Depends(get_manager),
):
    session = await manager.get_session(payload.session_id)
    page = await session.get_active_page()
    dom = await extract_compressed_dom(page)
    return {
        "success": True,
        "data": dom,
    }
