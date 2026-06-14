"""
SPECTR Plugin API — Decorator-based plugin system.

Usage:
    from core.plugin_api import plugin, on, post_load

    @plugin(
        name="My Plugin",
        version="1.0.0",
        description="A simple plugin",
        position="top",
        width=400,
        height=150,
        journal_events=["FSDJump", "Location"],
        status_events=True,
    )
    class MyPlugin:
        def create(self, ctx):
            self.label = ctx.add_label(text="Hello", fg=ctx.accent)

        @on("journal:FSDJump")
        def on_jump(self, ctx, data):
            self.label.config(text=data.get("StarSystem", ""))

        @post_load
        def on_ready(self, ctx):
            pass
"""

import tkinter as tk
import logging

logger = logging.getLogger(__name__)


class PluginContext:
    """
    Provides helpers and state to a plugin during its lifecycle.

    Attributes:
        event (str): The current event name being handled (e.g. "journal:FSDJump").
        font (tuple): Scaled font family and size, e.g. ("Consolas", 11).
        font_small (tuple): Smaller font for secondary text.
        bg (str): Background color from config.
        fg (str): Foreground color from config.
        accent (str): Accent color from config.
        config (Config): Application config object.
        game (Game): Game state tracker.
        status (Status): Parsed Status.json flags.
        overlay (Overlay): The overlay instance (for scheduling, resizing).
        pcfg (dict): This plugin's config section.
        win: The PluginPanel wrapper.
        parent: The tkinter container frame for this plugin.
        scale_factor (float): Resolution scale factor relative to 1920x1080.
    """

    def __init__(self, plugin_instance, event=None):
        self._plugin = plugin_instance
        self.event = event
        self.scale_factor = plugin_instance.overlay.scale_factor

    @property
    def font(self):
        return self._plugin.font

    @property
    def font_small(self):
        return self._plugin.font_small

    @property
    def bg(self):
        return self._plugin.bg

    @property
    def fg(self):
        return self._plugin.fg

    @property
    def accent(self):
        return self._plugin.accent

    @property
    def config(self):
        return self._plugin.config

    @property
    def game(self):
        return self._plugin.game

    @property
    def status(self):
        return self._plugin.status

    @property
    def overlay(self):
        return self._plugin.overlay

    @property
    def pcfg(self):
        return self._plugin.pcfg

    @property
    def win(self):
        return self._plugin.win

    @property
    def parent(self):
        return self._plugin.parent

    def add_label(self, text="", fg=None, anchor=None, font=None, pack=True, **kwargs):
        """Add a tk.Label to the plugin parent. Returns the label widget."""
        kw = {
            "text": text,
            "font": font or self.font,
            "bg": self.bg,
            "fg": fg or self.fg,
        }
        if anchor is not None:
            kw["anchor"] = anchor
        kw.update(kwargs)
        label = tk.Label(self.parent, **kw)
        if pack:
            label.pack(fill=tk.X)
        return label

    def add_canvas(self, width=None, height=None, **kwargs):
        """Add a tk.Canvas to the plugin parent. Returns the canvas widget."""
        sf = self.scale_factor
        kw = {
            "bg": self.bg,
            "highlightthickness": 0,
            "bd": 0,
        }
        if width is not None:
            kw["width"] = max(80, round(width * sf))
        if height is not None:
            kw["height"] = max(20, round(height * sf))
        kw.update(kwargs)
        canvas = tk.Canvas(self.parent, **kw)
        return canvas

    def add_frame(self, bg=None, **kwargs):
        """Add a tk.Frame to the plugin parent. Returns the frame widget."""
        kw = {"bg": bg or self.bg}
        kw.update(kwargs)
        return tk.Frame(self.parent, **kw)

    def add_separator(self, color="#333333", height=1):
        """Add a horizontal separator line."""
        sf = self.scale_factor
        sep = tk.Frame(self.parent, bg=color, height=max(1, round(height * sf)))
        sep.pack(fill=tk.X, pady=(0, 4))
        return sep

    def set_visible(self, visible):
        """Show or hide this plugin window."""
        self._plugin.overlay.set_panel_visible(self._plugin.name, visible)

    def resize(self):
        """Trigger a resize recalculation for this plugin."""
        self._plugin.overlay.resize_plugin(self._plugin.name)

    def set_width(self, width):
        """Dynamically set the panel width in unscaled pixels. Skips if user manually resized."""
        panel = self._plugin.overlay._plugin_panels.get(self._plugin.name)
        if panel and not panel._custom_size:
            sf = self._plugin.overlay._scale_factor
            panel._pl_w = max(100, round(width * sf))
            panel._place_kwargs["width"] = panel._pl_w
            if panel._shown:
                panel._frame.place(**panel._place_kwargs)
            panel._position_grip()

    def schedule(self, ms, callback):
        """Schedule a callback after ms milliseconds."""
        self._plugin.overlay.schedule(ms, callback)

    def notify(self, message, level="info", duration_ms=3000):
        """Show a toast notification on the overlay. Levels: info, success, warning, error."""
        self._plugin.overlay.notify(message, level, duration_ms)


def plugin(
    name,
    *,
    version="1.0.0",
    description="",
    position="top",
    width=300,
    height=150,
    max_height=None,
    offset_x=0,
    journal_events=None,
    status_events=False,
    dynamic=False,
    settings_tab=None,
    relative_to=None,
    relative_pos="bottom",
):
    """
    Decorator to register a plugin class.

    Args:
        name (str): Display name of the plugin.
        version (str): Semantic version string.
        description (str): Short description.
        position (str): Screen position — one of "top-left", "top", "top-right",
            "center-left", "center", "center-right", "bottom-left", "bottom",
            "bottom-right".
        width (int): Default panel width in pixels (scaled).
        height (int): Default panel height in pixels (scaled).
        max_height (int | None): Maximum height for auto-sizing panels.
        offset_x (int): Horizontal offset from the edge.
        journal_events (list[str]): Journal event names to subscribe to,
            e.g. ["FSDJump", "Location"]. Subscribed as "journal:<event>".
        status_events (bool): If True, subscribe to Status.json updates.
        dynamic (bool): If True, auto-hide when no relevant content.
        settings_tab (str | None): If set, creates a tab in the Settings window
            with this name. The plugin must define build_settings(self, parent,
            overlay, config) to populate the tab.
        relative_to (str | None): If set, position this panel relative to
            another plugin's panel (by name).
        relative_pos (str): Where to place relative to the anchor — one of
            "top", "bottom", "left", "right" (default "bottom").

    Returns:
        Class decorator.

    Example:
        @plugin(
            name="Jump Tracker",
            version="1.0.0",
            position="top",
            width=400,
            height=120,
            journal_events=["FSDJump", "Location", "NavRoute"],
        )
        class JumpTracker:
            def create(self, ctx):
                self.label = ctx.add_label(text="", fg=ctx.accent)

            @on("journal:FSDJump")
            def on_jump(self, ctx, data):
                self.label.config(text=data.get("StarSystem", ""))
    """
    if journal_events is None:
        journal_events = []

    def decorator(cls):
        if settings_tab is None and not callable(getattr(cls, "create", None)):
            raise TypeError(
                f"Plugin '{name}' must define a 'create(self, ctx)' method "
                f"or set settings_tab"
            )

        cls._plugin_meta = {
            "name": name,
            "version": version,
            "description": description,
            "position": position,
            "width": width,
            "height": height,
            "max_height": max_height,
            "offset_x": offset_x,
            "journal_events": list(journal_events),
            "status_events": status_events,
            "dynamic": dynamic,
            "settings_tab": settings_tab,
            "relative_to": relative_to,
            "relative_pos": relative_pos,
        }
        return cls

    return decorator


def on(*event_names):
    """
    Decorator to register an event handler.

    Args:
        *event_names: One or more event strings, e.g.
            "journal:FSDJump", "journal:Location", "status".

    Returns:
        Method decorator.

    Example:
        @on("journal:FSDJump", "journal:Location")
        def on_system_change(self, ctx, data):
            self.label.config(text=data.get("StarSystem", ""))

        @on("status")
        def on_status(self, ctx, data):
            flags = data.get("Flags", 0)
            self._in_combat = bool(flags & HARDPOINTS)
    """
    def decorator(fn):
        if not hasattr(fn, "_event_handlers"):
            fn._event_handlers = []
        fn._event_handlers.extend(event_names)
        return fn
    return decorator


def post_load(fn):
    """
    Decorator to register a post-load hook.

    Called after the plugin's create() method and all event subscriptions
    are set up. Use for state restoration, polling setup, or initial data loads.

    Returns:
        Method decorator.

    Example:
        @post_load
        def on_ready(self, ctx):
            self._restore_state_from_journal()
            self._poll_navroute()
    """
    fn._is_post_load = True
    return fn


def _collect_event_handlers(cls):
    """Collect all @on-decorated methods from a class. Returns dict mapping event -> [methods]."""
    handlers = {}
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name, None)
        if attr is None or not callable(attr):
            continue
        event_list = getattr(attr, "_event_handlers", [])
        for event in event_list:
            handlers.setdefault(event, []).append(attr_name)
    return handlers


def _find_post_load(cls):
    """Find the @post_load method name on a class, or None."""
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name, None)
        if attr is not None and getattr(attr, "_is_post_load", False):
            return attr_name
    return None
