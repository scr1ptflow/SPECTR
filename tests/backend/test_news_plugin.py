"""Tests for the news plugin."""

import asyncio
import pytest
from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine
from plugins.news import NewsPlugin


@pytest.mark.asyncio
async def test_news_plugin_generates_jump_news():
    plugin = NewsPlugin()
    bus = EventBus()
    state = StateEngine(bus)
    await plugin.setup(bus, state)

    await bus.publish(Event(
        topic="journal.fsdjump",
        data={"StarSystem": "Sol"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    news = plugin.recent_news
    assert len(news) >= 1
    assert "Sol" in news[0]["headline"]
    assert news[0]["category"] == "navigation"


@pytest.mark.asyncio
async def test_news_plugin_generates_dock_news():
    plugin = NewsPlugin()
    bus = EventBus()
    state = StateEngine(bus)
    await plugin.setup(bus, state)

    await bus.publish(Event(
        topic="journal.docked",
        data={"StationName": "Galileo"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    news = plugin.recent_news
    assert len(news) >= 1
    assert "Galileo" in news[0]["headline"]
    assert news[0]["category"] == "navigation"


@pytest.mark.asyncio
async def test_news_plugin_generates_organic_news():
    plugin = NewsPlugin()
    bus = EventBus()
    state = StateEngine(bus)
    await plugin.setup(bus, state)

    await bus.publish(Event(
        topic="journal.scanorganic",
        data={"Species": "Stratum Tectonicas", "Body": "Earth"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    news = plugin.recent_news
    assert len(news) >= 1
    assert "Stratum Tectonicas" in news[0]["headline"]
    assert news[0]["category"] == "exobiology"


@pytest.mark.asyncio
async def test_news_plugin_teardown():
    plugin = NewsPlugin()
    bus = EventBus()
    state = StateEngine(bus)
    await plugin.setup(bus, state)

    await bus.publish(Event(
        topic="journal.fsdjump",
        data={"StarSystem": "Sol"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    assert len(plugin.recent_news) > 0
    await plugin.teardown()
    assert len(plugin.recent_news) == 0
