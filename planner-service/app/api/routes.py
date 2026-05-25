import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.dependencies import EventBusDep, PlannerEngineDep, SessionStoreDep
from app.memory.store import SessionNotFoundError
from app.schemas.agent import (
    AgentStartResponse,
    AgentStatusResponse,
    CancelAgentResponse,
    ContinueAgentRequest,
    StartAgentRequest,
)
from app.schemas.state import AgentSession

router = APIRouter(prefix="/agent", tags=["agent"])


def _status_response(session: AgentSession) -> AgentStatusResponse:
    return AgentStatusResponse(
        session_id=session.session_id,
        goal=session.goal,
        state=session.state,
        current_step=session.current_step,
        plan_summary=session.plan_summary,
        final_result=session.final_result,
        error=session.error,
        timeline=[event.model_dump(mode="json") for event in session.timeline],
        metadata=session.metadata | {"token_usage": session.token_usage},
    )


@router.post("/start", response_model=AgentStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_agent(request: StartAgentRequest, engine: PlannerEngineDep) -> AgentStartResponse:
    session = await engine.start(goal=request.goal, metadata=request.metadata)
    return AgentStartResponse(session_id=session.session_id, state=session.state)


@router.post("/{session_id}/continue", response_model=AgentStatusResponse)
async def continue_agent(
    session_id: str,
    request: ContinueAgentRequest,
    engine: PlannerEngineDep,
) -> AgentStatusResponse:
    try:
        session = await engine.continue_session(session_id, request.user_input)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return _status_response(session)


@router.get("/{session_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(session_id: str, store: SessionStoreDep) -> AgentStatusResponse:
    try:
        session = await store.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return _status_response(session)


@router.post("/{session_id}/cancel", response_model=CancelAgentResponse)
async def cancel_agent(session_id: str, engine: PlannerEngineDep) -> CancelAgentResponse:
    try:
        session = await engine.cancel(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return CancelAgentResponse(session_id=session.session_id, state=session.state)


@router.websocket("/{session_id}/stream")
async def stream_agent(session_id: str, websocket: WebSocket, events: EventBusDep) -> None:
    await websocket.accept()
    queue = await events.subscribe(session_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event.model_dump(mode="json"))
            except TimeoutError:
                await websocket.send_json({"type": "heartbeat", "session_id": session_id})
    except WebSocketDisconnect:
        pass
    finally:
        await events.unsubscribe(session_id, queue)
