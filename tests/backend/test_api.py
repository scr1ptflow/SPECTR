"""Tests for the API server."""

import pytest
from starlette.testclient import TestClient

from bridge_core.api.server import create_app
from bridge_core.events.bus import EventBus
from bridge_core.state.engine import StateEngine


@pytest.fixture
def client():
    bus = EventBus()
    state = StateEngine(bus)
    app = create_app(state, bus)
    return TestClient(app)


def test_get_bridge(client):
    response = client.get("/api/v1/bridge")
    assert response.status_code == 200
    data = response.json()
    assert "captain_briefing" in data
    assert "ship_status" in data
    assert "current_mission" in data
    assert "department_status" in data
    assert "current_location" in data
    assert "alerts" in data
    assert "recommendations" in data
    assert "expedition_summary" in data
    assert "captains_log" in data
    assert "generated" in data
    assert data["captain_briefing"]["status"] in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert isinstance(data["department_status"], list)
    assert len(data["department_status"]) == 9


def test_get_commander(client):
    response = client.get("/api/v1/commander")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "commander"
    assert "status" in data
    assert "summary" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_navigation(client):
    response = client.get("/api/v1/navigation")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "navigation"
    assert "status" in data
    assert "summary" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_ship(client):
    response = client.get("/api/v1/ship")
    assert response.status_code == 200
    data = response.json()
    assert "ship_type" in data


def test_get_missions(client):
    response = client.get("/api/v1/missions")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "operations"
    assert "status" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_scans(client):
    response = client.get("/api/v1/scans")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "laboratory"
    assert "status" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_engineering(client):
    response = client.get("/api/v1/engineering")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "engineering"
    assert "status" in data
    assert "summary" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_ranks(client):
    response = client.get("/api/v1/ranks")
    assert response.status_code == 200
    data = response.json()
    assert "combat" in data


def test_get_cargo(client):
    response = client.get("/api/v1/cargo")
    assert response.status_code == 200


def test_get_archive(client):
    response = client.get("/api/v1/archive")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "archive"
    assert "status" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data


def test_get_intelligence(client):
    response = client.get("/api/v1/intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "intelligence"
    assert "status" in data
    assert "summary" in data
    assert "findings" in data
    assert "recommendations" in data
    assert "details" in data
    assert "history" in data
