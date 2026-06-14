import logging

from .plugin_api import PluginContext, _collect_event_handlers, _find_post_load

logger = logging.getLogger(__name__)


class Plugin:
    name = "Unnamed Plugin"
    version = "1.0.0"
    description = ""
    author = ""

    # Plugin window defaults — override per plugin
    window_position = "top"
    window_width = 300
    window_height = 150
    window_max_height = None
    window_offset_x = 0

    # Events to auto-subscribe (override per plugin)
    journal_events = []
    status_events = False

    # Set by wrapper for settings-only plugins (no overlay panel)
    _settings_only = False

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.config = config
        self.game = game
        self.status = status
        self.pcfg = config.plugin_config(self.name)

        self.font_family = config.get("overlay", "font_family", default="Consolas")
        self._scaled_size = overlay._scaled_font_size
        self.font = (self.font_family, self._scaled_size)
        self.font_small = (self.font_family, max(self._scaled_size - 2, 8))
        self.bg = config.get("overlay", "bg_color", default="#0a0f08")
        self.accent = config.get("overlay", "accent_color", default="#00d4aa")
        self.fg = config.get("overlay", "fg_color", default="#e0e0e0")

        if not self._settings_only:
            self._create_window_common()
            self.create_widgets(self.parent)
            self.win.attributes("-alpha", 1.0)

        for evt in self.journal_events:
            event_bus.subscribe(f"journal:{evt}", self.on_event)
        if self.status_events:
            event_bus.subscribe("status", self.on_event)

        self.post_load()

    def _create_context(self, event=None):
        """Create a PluginContext wrapping this plugin instance."""
        return PluginContext(self, event=event)

    def _create_window_common(self):
        win_pos = self.pcfg.get("window_position", self.window_position)
        win_w = self.pcfg.get("window_width", self.window_width)
        win_h = self.pcfg.get("window_height", self.window_height)
        rel_to = getattr(self, "_relative_to", None)
        rel_pos = getattr(self, "_relative_pos", "bottom")
        self.win = self.overlay.create_plugin_window(
            self.name, position=win_pos, width=win_w, height=win_h,
            max_height=self.window_max_height, offset_x=self.window_offset_x,
            relative_to=rel_to, relative_pos=rel_pos,
        )
        self.parent = self.win.container

    def create_widgets(self, parent):
        """Build plugin widgets. Called during on_load."""

    def post_load(self):
        """Called after widgets created and events subscribed.
        Override for state restoration, polling, etc."""

    def on_unload(self):
        self._cleanup_window()
        self._cleanup_subscriptions()

    def _cleanup_window(self):
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass

    def _cleanup_subscriptions(self):
        if hasattr(self, "event_bus"):
            for evt in self.journal_events:
                self.event_bus.unsubscribe(f"journal:{evt}", self.on_event)
            if self.status_events:
                self.event_bus.unsubscribe("status", self.on_event)

    def on_event(self, event, data):
        pass

    def set_visible(self, visible):
        if hasattr(self, "overlay"):
            self.overlay.set_panel_visible(self.name, visible)

    def resize(self):
        if hasattr(self, "win") and hasattr(self, "overlay"):
            self.overlay.resize_plugin(self.name)
