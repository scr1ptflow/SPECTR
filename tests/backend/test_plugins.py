"""Tests for the plugin system."""

import pytest
from bridge_core.events.bus import EventBus
from bridge_core.state.engine import StateEngine
from bridge_core.plugins.base import BasePlugin
from bridge_core.plugins.manager import PluginManager


class MockPlugin(BasePlugin):
    name = "mock"
    version = "0.1.0"
    setup_called = False
    teardown_called = False

    async def setup(self, bus, state, db=None):
        MockPlugin.setup_called = True
        self.bus = bus

    async def teardown(self):
        MockPlugin.teardown_called = True


class FailingPlugin(BasePlugin):
    name = "failing"
    version = "0.1.0"

    async def setup(self, bus, state, db=None):
        raise RuntimeError("Setup failed!")

    async def teardown(self):
        raise RuntimeError("Teardown failed!")


def test_register_plugin():
    manager = PluginManager()
    plugin = MockPlugin()
    manager.register(plugin)
    assert manager.plugin_count == 1
    assert manager.get_plugin("mock") is plugin


def test_register_duplicate():
    manager = PluginManager()
    manager.register(MockPlugin())
    manager.register(MockPlugin())
    assert manager.plugin_count == 1


@pytest.mark.asyncio
async def test_setup_all():
    manager = PluginManager()
    manager.register(MockPlugin())
    bus = EventBus()
    state = StateEngine(bus)
    await manager.setup_all(bus, state)
    assert MockPlugin.setup_called


@pytest.mark.asyncio
async def test_teardown_all():
    manager = PluginManager()
    manager.register(MockPlugin())
    bus = EventBus()
    state = StateEngine(bus)
    await manager.setup_all(bus, state)
    await manager.teardown_all()
    assert MockPlugin.teardown_called


@pytest.mark.asyncio
async def test_setup_failure_does_not_crash():
    manager = PluginManager()
    manager.register(FailingPlugin())
    bus = EventBus()
    state = StateEngine(bus)
    await manager.setup_all(bus, state)  # should not raise
    assert manager.plugin_count == 1


@pytest.mark.asyncio
async def test_teardown_failure_does_not_crash():
    manager = PluginManager()
    manager.register(FailingPlugin())
    await manager.teardown_all()  # should not raise
