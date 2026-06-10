import logging

from .event_bus import EventBus
from .journal import JournalMonitor
from .overlay import Overlay
from .plugin_manager import PluginManager
from .config import Config
from .status import Status
from .game import Game
from .window import GameWindow

logger = logging.getLogger(__name__)


class App:
    _WINDOW_POLL_MS = 200

    def __init__(self):
        self.config = Config()
        self.event_bus = EventBus()
        self.status = Status()
        self.game_window = GameWindow()
        self.overlay = Overlay(self.config)
        self.plugin_manager = PluginManager()
        self.game = None
        self.journal = None

    def initialize(self):
        journal_path = self.config.get("journal_path")

        self.journal = JournalMonitor(
            self.event_bus,
            journal_path=journal_path,
            poll_interval=self.config.get("journal", "poll_interval", default=0.5),
        )

        self.game = Game(self.event_bus, self.journal.journal_dir)

        self.overlay.plugin_manager = self.plugin_manager
        self.overlay.set_shutdown_hook(self.shutdown)

        self.plugin_manager.load_all(self.overlay, self.event_bus, self.config,
                                     self.game, self.status)

        self.event_bus.subscribe("journal", self._on_journal_event)
        self.event_bus.subscribe("status", self._on_status_event)

        self.overlay.hide_all_extra()
        self.journal.replay_all()
        while self.event_bus.process_queue() > 0:
            pass
        self.overlay.show_all_extra()

        self.journal.start_async()

        self._schedule_event_processing()
        self._schedule_window_poll()

    def _on_journal_event(self, event, data):
        if self.game:
            self.game.handle_journal_event(data.get("event", ""), data)

    def _on_status_event(self, event, data):
        if self.status:
            self.status.update(data)
        self.overlay.set_gui_focus(data.get("GuiFocus", 0))

    def _schedule_event_processing(self):
        self.event_bus.process_queue()
        self.overlay.enforce_game_focus()
        self.overlay.enforce_gui_focus()
        self.overlay.schedule(50, self._schedule_event_processing)

    def _schedule_window_poll(self):
        try:
            rect, changed = self.game_window.poll()
            if rect and changed:
                self.overlay.reposition_on_game(rect)
            focused = self.game_window.is_focused()
            self.overlay.set_game_focused(focused)
        except Exception as e:
            logger.debug(f"Window poll error: {e}")
        self.overlay.schedule(self._WINDOW_POLL_MS, self._schedule_window_poll)

    def run(self):
        self.initialize()
        self.overlay.start()

    def shutdown(self):
        if self.journal:
            self.journal.stop()
        self.overlay._on_close()
