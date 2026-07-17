"""Elite Bridge Core — application entry point.

Bootstraps all subsystems and starts the API server.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import uvicorn

from bridge_core.api.server import create_app
from bridge_core.config.settings import Settings
from bridge_core.database.db import Database
from bridge_core.events.bus import EventBus
from bridge_core.journal.watcher import JournalWatcher
from bridge_core.plugins.manager import PluginManager
from bridge_core.services.session_manager import SessionManager
from bridge_core.state.engine import StateEngine

log = logging.getLogger("bridge_core")


async def run(settings: Settings) -> None:
    bus = EventBus()
    state = StateEngine(bus)
    watcher = JournalWatcher(settings.journal_path, bus)

    # Database
    db = Database(settings.database_path)
    await db.connect()

    # Session manager
    session_mgr = SessionManager(bus, db)

    # Plugin manager
    plugin_mgr = PluginManager()

    # Discover and load plugins
    from pathlib import Path

    plugin_dir = Path(__file__).parent.parent.parent / "plugins"
    if plugin_dir.exists():
        count = plugin_mgr.discover_plugins(plugin_dir)
        log.info("Discovered %d plugin(s).", count)

    await plugin_mgr.setup_all(bus, state, db)

    app = create_app(state, bus)
    app.state.session_manager = session_mgr

    config = uvicorn.Config(app, host="127.0.0.1", port=8420, log_level="info")
    server = uvicorn.Server(config)

    log.info("Elite Bridge Core starting...")
    log.info("Journal path: %s", settings.journal_path)
    log.info("Database: %s", settings.database_path)

    try:
        await asyncio.gather(
            watcher.run(),
            server.serve(),
        )
    finally:
        await plugin_mgr.teardown_all()
        await db.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    settings = Settings.load()

    try:
        asyncio.run(run(settings))
    except KeyboardInterrupt:
        log.info("Elite Bridge Core shutting down.")
        sys.exit(0)


if __name__ == "__main__":
    main()
