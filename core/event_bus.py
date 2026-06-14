from collections import defaultdict
from types import MappingProxyType
import queue
import logging
import traceback

logger = logging.getLogger(__name__)

_EMPTY = MappingProxyType({})


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._wildcards = []
        self._queue = queue.Queue()

    def subscribe(self, event, callback):
        if event == "*":
            self._wildcards.append(callback)
        else:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event, callback):
        if event == "*":
            if callback in self._wildcards:
                self._wildcards.remove(callback)
        else:
            handlers = self._subscribers.get(event, [])
            if callback in handlers:
                handlers.remove(callback)

    def publish(self, event, data=None):
        self._queue.put((event, data if data is not None else _EMPTY))

    def process_queue(self, max_events=200):
        processed = 0
        try:
            while processed < max_events:
                event, data = self._queue.get_nowait()
                for cb in self._subscribers.get(event, []):
                    try:
                        cb(event, data)
                    except Exception as e:
                        logger.error(f"Error in subscriber for {event}: {e}\n{traceback.format_exc()}")
                for cb in self._wildcards[:]:
                    try:
                        cb(event, data)
                    except Exception as e:
                        logger.error(f"Error in wildcard subscriber: {e}\n{traceback.format_exc()}")
                processed += 1
        except queue.Empty:
            pass
        return processed
