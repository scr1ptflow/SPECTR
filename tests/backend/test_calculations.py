"""Tests for the calculations layer."""

from bridge_core.calculations.exploration import (
    predict_scan_value,
    predict_biological_value,
)
from bridge_core.calculations.risk import assess_system_risk, assess_docking_risk
from bridge_core.calculations.travel import compute_travel_stats


def test_scan_value_earthlike():
    val = predict_scan_value("Earthlike body")
    assert val > 0
    assert val > predict_scan_value("Rocky body")


def test_scan_value_gas_giant():
    val = predict_scan_value("Gas giant with water based life")
    assert val > 0


def test_scan_value_mapped():
    mapped = predict_scan_value("Earthlike body", is_mapped=True)
    unmapped = predict_scan_value("Earthlike body", is_mapped=False)
    assert mapped > unmapped


def test_biological_value():
    val = predict_biological_value("Stratum Tectonicas", 2)
    assert val == 4_848_500 * 2


def test_biological_value_unknown():
    val = predict_biological_value("Unknown Species", 1)
    assert val == 0


def test_risk_low_security():
    result = assess_system_risk("Low", 0)
    assert result["level"] in ("low", "medium")
    assert result["score"] < 50


def test_risk_anarchy():
    result = assess_system_risk("Anarchy", 0)
    assert result["score"] >= 40
    assert "Anarchy system" in result["factors"]


def test_risk_notoriety():
    result = assess_system_risk("Medium", 5)
    assert result["score"] > 0
    assert any("Notoriety" in f for f in result["factors"])


def test_docking_risk_low():
    result = assess_docking_risk("Orbital Starport", "M", 0)
    assert result["level"] == "low"


def test_docking_risk_high_notoriety():
    result = assess_docking_risk("Orbital Starport", "M", 5)
    assert result["level"] in ("medium", "high")


def test_travel_stats():
    stats = compute_travel_stats(
        jump_count=10, total_distance=250.5,
        bodies_scanned=5, organic_scans=3,
    )
    assert stats.total_jumps == 10
    assert stats.total_distance_ly == 250.5
    assert stats.average_jump_ly == 25.05
    assert stats.bodies_scanned == 5
