"""Tests for the event bus."""

import asyncio
import pytest
from bridge_core.events.bus import Event, EventBus


@pytest.mark.asyncio
async def test_publish_subscribe():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe("test.topic", handler)
    await bus.publish(Event(topic="test.topic", data={"value": 42}))

    # Process the queue
    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert len(received) == 1
    assert received[0].data["value"] == 42


@pytest.mark.asyncio
async def test_wildcard_handler():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event.topic)

    bus.subscribe_all(handler)
    await bus.publish(Event(topic="a.b"))
    await bus.publish(Event(topic="c.d"))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert "a.b" in received
    assert "c.d" in received


@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe("test.topic", handler)
    bus.unsubscribe("test.topic", handler)
    await bus.publish(Event(topic="test.topic"))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert len(received) == 0


@pytest.mark.asyncio
async def test_handler_exception_does_not_crash():
    bus = EventBus()
    received = []

    async def bad_handler(event: Event):
        raise ValueError("boom")

    async def good_handler(event: Event):
        received.append(event)

    bus.subscribe("test.topic", bad_handler)
    bus.subscribe("test.topic", good_handler)
    await bus.publish(Event(topic="test.topic", data={"ok": True}))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert len(received) == 1
