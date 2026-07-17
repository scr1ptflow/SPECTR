"""API server for Elite Bridge Core.

Creates the Starlette application with versioned REST endpoints
and WebSocket support for real-time updates.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# REST endpoints (v1)
# ---------------------------------------------------------------------------


async def get_bridge(request: Request) -> JSONResponse:
    """GET /api/v1/bridge — aggregated Bridge overview.

    The Bridge Department owns no data. It aggregates information
    from all other departments into a single situational awareness view.
    """
    from bridge_core.services.bridge import BridgeService
    state: StateEngine = request.app.state.state_engine
    svc = BridgeService(state)
    return JSONResponse(svc.get_report())


async def get_commander(request: Request) -> JSONResponse:
    """GET /api/v1/commander — Commander Officer Report."""
    from bridge_core.services.commander import CommanderService
    state: StateEngine = request.app.state.state_engine
    svc = CommanderService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_navigation(request: Request) -> JSONResponse:
    """GET /api/v1/navigation — Navigation Officer Report."""
    from bridge_core.services.navigation import NavigationService
    state: StateEngine = request.app.state.state_engine
    svc = NavigationService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_ship(request: Request) -> JSONResponse:
    """GET /api/v1/ship — ship state."""
    import dataclasses
    state: StateEngine = request.app.state.state_engine
    return JSONResponse(dataclasses.asdict(state.snapshot.ship))


async def get_missions(request: Request) -> JSONResponse:
    """GET /api/v1/missions — Operations Officer Report."""
    from bridge_core.services.operations import OperationsService
    state: StateEngine = request.app.state.state_engine
    svc = OperationsService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_scans(request: Request) -> JSONResponse:
    """GET /api/v1/scans — Laboratory Officer Report."""
    from bridge_core.services.laboratory import LaboratoryService
    state: StateEngine = request.app.state.state_engine
    svc = LaboratoryService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_engineering(request: Request) -> JSONResponse:
    """GET /api/v1/engineering — Engineering Officer Report."""
    from bridge_core.services.engineering import EngineeringService
    state: StateEngine = request.app.state.state_engine
    svc = EngineeringService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_ranks(request: Request) -> JSONResponse:
    """GET /api/v1/ranks — rank state."""
    import dataclasses
    state: StateEngine = request.app.state.state_engine
    return JSONResponse(dataclasses.asdict(state.snapshot.ranks))


async def get_cargo(request: Request) -> JSONResponse:
    """GET /api/v1/cargo — cargo state."""
    import dataclasses
    state: StateEngine = request.app.state.state_engine
    return JSONResponse(dataclasses.asdict(state.snapshot.cargo))


async def get_session(request: Request) -> JSONResponse:
    """GET /api/v1/session — current session stats."""
    from bridge_core.services.session_manager import SessionManager
    sm: SessionManager | None = getattr(request.app.state, "session_manager", None)
    if sm:
        return JSONResponse(sm.snapshot_dict())
    return JSONResponse({"active": False})


async def get_archive(request: Request) -> JSONResponse:
    """GET /api/v1/archive — Archive Officer Report."""
    from bridge_core.services.archive import ArchiveService
    state: StateEngine = request.app.state.state_engine
    svc = ArchiveService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


async def get_intelligence(request: Request) -> JSONResponse:
    """GET /api/v1/intelligence — Intelligence Officer Report."""
    from bridge_core.services.intelligence import IntelligenceService
    state: StateEngine = request.app.state.state_engine
    svc = IntelligenceService(state)
    report = svc.get_report()
    return JSONResponse(report.to_dict())


# ---------------------------------------------------------------------------
# WebSocket — real-time event stream
# ---------------------------------------------------------------------------

active_websockets: list[WebSocket] = []


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time state updates.

    Clients connect once and receive state.updated events whenever
    the game state changes.
    """
    await websocket.accept()
    active_websockets.append(websocket)
    log.info("WebSocket client connected. Total: %d", len(active_websockets))

    bus: EventBus = websocket.app.state.bus

    async def broadcast_handler(event: Event) -> None:
        if event.source != "journal":
            return
        message = json.dumps({
            "type": "state.updated",
            "topic": event.topic,
            "timestamp": event.timestamp.isoformat(),
        })
        disconnected = []
        for ws in active_websockets:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            active_websockets.remove(ws)

    bus.subscribe_all(broadcast_handler)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_text()
            # Client can request full state refresh
            if data == "refresh":
                state: StateEngine = websocket.app.state.state_engine
                await websocket.send_text(json.dumps({
                    "type": "state.full",
                    "data": state.snapshot_dict(),
                }))
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        log.info("WebSocket client disconnected. Total: %d", len(active_websockets))


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


STATIC_DIR = Path(__file__).parent.parent / "static"


class SPAStaticFiles(StaticFiles):
    """StaticFiles with SPA fallback — serves index.html for unknown paths."""

    async def get_response(self, path: str, scope: dict) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException:
            if scope["type"] == "http":
                index = Path(self.directory) / "index.html"
                if index.is_file():
                    return FileResponse(index)
            raise


def create_app(state_engine: StateEngine, bus: EventBus) -> Starlette:
    """Create the Starlette application with all routes."""

    routes = [
        Route("/api/v1/bridge", get_bridge, methods=["GET"]),
        Route("/api/v1/commander", get_commander, methods=["GET"]),
        Route("/api/v1/navigation", get_navigation, methods=["GET"]),
        Route("/api/v1/ship", get_ship, methods=["GET"]),
        Route("/api/v1/missions", get_missions, methods=["GET"]),
        Route("/api/v1/scans", get_scans, methods=["GET"]),
        Route("/api/v1/engineering", get_engineering, methods=["GET"]),
        Route("/api/v1/ranks", get_ranks, methods=["GET"]),
        Route("/api/v1/cargo", get_cargo, methods=["GET"]),
        Route("/api/v1/session", get_session, methods=["GET"]),
        Route("/api/v1/archive", get_archive, methods=["GET"]),
        Route("/api/v1/intelligence", get_intelligence, methods=["GET"]),
        WebSocketRoute("/ws", websocket_endpoint),
    ]

    if STATIC_DIR.is_dir():
        routes.append(
            Mount("/", app=SPAStaticFiles(directory=str(STATIC_DIR), html=True))
        )

    app = Starlette(routes=routes)
    app.state.state_engine = state_engine
    app.state.bus = bus
    app.state.session_manager = None
    app.state.intelligence_service = None

    return app
