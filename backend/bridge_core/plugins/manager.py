"""Plugin manager for Elite Bridge Core.

Discovers, loads, starts, and stops plugins.
Plugins are registered with the manager and receive access to the bus,
state engine, and database on setup.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bridge_core.plugins.base import BasePlugin

if TYPE_CHECKING:
    from bridge_core.database.db import Database
    from bridge_core.events.bus import EventBus
    from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class PluginManager:
    """Manages the lifecycle of all plugins.

    Usage:
        manager = PluginManager()
        manager.register(MyPlugin())
        await manager.setup_all(bus, state, db)
        await manager.teardown_all()
    """

    def __init__(self) -> None:
        self._plugins: list[BasePlugin] = []
        self._loaded: set[str] = set()

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin instance."""
        if plugin.name in self._loaded:
            log.warning("Plugin '%s' already registered, skipping.", plugin.name)
            return
        self._plugins.append(plugin)
        self._loaded.add(plugin.name)
        log.info("Registered plugin: %s v%s", plugin.name, plugin.version)

    def register_class(self, plugin_cls: type[BasePlugin]) -> None:
        """Register a plugin by class (instantiates it)."""
        self.register(plugin_cls())

    async def setup_all(
        self,
        bus: EventBus,
        state: StateEngine,
        db: Database | None = None,
    ) -> None:
        """Set up all registered plugins."""
        for plugin in self._plugins:
            try:
                plugin.bus = bus
                plugin.state = state
                plugin.db = db
                await plugin.setup(bus, state, db)
                log.info("Plugin '%s' setup complete.", plugin.name)
            except Exception:
                log.exception("Plugin '%s' setup failed.", plugin.name)

    async def teardown_all(self) -> None:
        """Tear down all registered plugins in reverse order."""
        for plugin in reversed(self._plugins):
            try:
                await plugin.teardown()
                log.info("Plugin '%s' teardown complete.", plugin.name)
            except Exception:
                log.exception("Plugin '%s' teardown failed.", plugin.name)

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a plugin by name."""
        for p in self._plugins:
            if p.name == name:
                return p
        return None

    @property
    def plugins(self) -> list[BasePlugin]:
        return list(self._plugins)

    @property
    def plugin_count(self) -> int:
        return len(self._plugins)

    def discover_plugins(self, plugin_dir: str | Path) -> int:
        """Discover and register plugins from a directory.

        Looks for Python files with a module-level `plugin_class` attribute
        that is a subclass of BasePlugin.

        Returns the number of newly registered plugins.
        """
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            log.warning("Plugin directory does not exist: %s", plugin_path)
            return 0

        count = 0
        for py_file in plugin_path.glob("*/__init__.py"):
            module_name = py_file.parent.name
            if module_name in self._loaded:
                continue

            try:
                module = importlib.import_module(f"plugins.{module_name}")
                plugin_class = getattr(module, "plugin_class", None)

                if plugin_class and (
                    isinstance(plugin_class, type) and issubclass(plugin_class, BasePlugin)
                ):
                    self.register_class(plugin_class)
                    count += 1
                    log.info("Discovered plugin: %s", module_name)
            except Exception:
                log.exception("Failed to load plugin: %s", module_name)

        return count
