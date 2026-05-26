from typing import Annotated, cast

from fastapi import Depends, Request, WebSocket

from app.memory.store import SessionStore
from app.planner.engine import PlannerEngine
from app.streaming.event_bus import EventBus


def get_engine(request: Request) -> PlannerEngine:
    return cast(PlannerEngine, request.app.state.planner_engine)


def get_store(request: Request) -> SessionStore:
    return cast(SessionStore, request.app.state.session_store)


def get_event_bus(request: Request) -> EventBus:
    return cast(EventBus, request.app.state.event_bus)


def get_websocket_event_bus(websocket: WebSocket) -> EventBus:
    return cast(EventBus, websocket.app.state.event_bus)


PlannerEngineDep = Annotated[PlannerEngine, Depends(get_engine)]
SessionStoreDep = Annotated[SessionStore, Depends(get_store)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
WebSocketEventBusDep = Annotated[EventBus, Depends(get_websocket_event_bus)]
