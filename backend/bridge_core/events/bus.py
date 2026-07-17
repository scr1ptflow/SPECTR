"""Internal event bus for Elite Bridge Core.

All subsystems communicate through events. No subsystem calls another directly.
Events are typed and dispatched to registered handlers asynchronously.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

log = logging.getLogger(__name__)

Handler = Callable[["Event"], Coroutine[Any, Any, None]]


@dataclass
class Event:
    """An internal event broadcast on the bus."""

    topic: str
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = ""


class EventBus:
    """Async publish-subscribe event bus.

    Usage:
        bus = EventBus()
        bus.subscribe("journal.fsd_jump", my_handler)
        await bus.publish(Event(topic="journal.fsd_jump", data={...}))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._wildcard_handlers: list[Handler] = []
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register a handler for a specific topic."""
        self._handlers[topic].append(handler)
        log.debug("Subscribed %s to %s", handler.__qualname__, topic)

    def subscribe_all(self, handler: Handler) -> None:
        """Register a handler for all events."""
        self._wildcard_handlers.append(handler)
        log.debug("Subscribed %s to all topics", handler.__qualname__)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        """Remove a handler from a topic."""
        handlers = self._handlers.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        await self._queue.put(event)

    def publish_sync(self, event: Event) -> None:
        """Publish an event without waiting (for non-async contexts)."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            log.warning("Event bus queue full, dropping event: %s", event.topic)

    async def run(self) -> None:
        """Main event processing loop. Call from the application runner."""
        self._running = True
        log.info("Event bus started.")
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except TimeoutError:
                continue

            handlers = list(self._handlers.get(event.topic, []))
            handlers.extend(self._wildcard_handlers)

            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    log.exception(
                        "Handler %s failed for event %s",
                        handler.__qualname__,
                        event.topic,
                    )

    def stop(self) -> None:
        """Signal the bus to stop processing."""
        self._running = False
