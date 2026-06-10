import importlib
import importlib.util
import inspect
import os
import re
import sys
import logging
import traceback

from .plugin_base import Plugin

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self):
        self._plugins = {}
        self._plugin_dir = self._find_plugin_dir()
        self._name_to_dir = {}

    def _find_plugin_dir(self):
        core_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(core_dir)
        return os.path.join(root_dir, "plugins")

    def _scan_name_to_dir(self):
        self._name_to_dir = {}
        if not os.path.isdir(self._plugin_dir):
            return
        for entry in sorted(os.listdir(self._plugin_dir)):
            plugin_path = os.path.join(self._plugin_dir, entry)
            if not os.path.isdir(plugin_path):
                continue
            plugin_file = os.path.join(plugin_path, "plugin.py")
            if not os.path.isfile(plugin_file):
                continue
            try:
                with open(plugin_file, encoding="utf-8") as f:
                    src = f.read()
                m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', src)
                if m:
                    self._name_to_dir[m.group(1)] = entry
            except OSError:
                continue

    def load_all(self, overlay, event_bus, config, game=None, status=None):
        if not os.path.isdir(self._plugin_dir):
            return

        sys.path.insert(0, os.path.dirname(self._plugin_dir))
        self._scan_name_to_dir()

        for entry in sorted(os.listdir(self._plugin_dir)):
            plugin_path = os.path.join(self._plugin_dir, entry)
            if not os.path.isdir(plugin_path):
                continue
            plugin_file = os.path.join(plugin_path, "plugin.py")
            if not os.path.isfile(plugin_file):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{entry}.plugin", plugin_file
                )
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin:
                        instance = obj()
                        plugin_config = config.plugin_config(instance.name)
                        if not plugin_config.get("enabled", True):
                            logger.info(f"Plugin disabled: {instance.name}")
                            continue
                        instance.on_load(overlay, event_bus, config, game, status)
                        self._plugins[instance.name] = instance
                        logger.info(
                            f"Loaded plugin: {instance.name} v{instance.version}"
                        )
                        break
            except Exception as e:
                logger.error(
                    f"Failed to load plugin {entry}: {e}\n{traceback.format_exc()}"
                )

    def unload_plugin(self, name, overlay=None):
        plugin = self._plugins.pop(name, None)
        if not plugin:
            return False
        try:
            plugin.on_unload()
            logger.info(f"Unloaded plugin: {name}")
        except Exception as e:
            logger.error(f"Error unloading plugin {name}: {e}")
        if overlay:
            overlay.remove_plugin_container(name)
            overlay.remove_plugin_window(name)
        return True

    def unload_all(self, overlay=None):
        for name in list(self._plugins.keys()):
            self.unload_plugin(name, overlay)

    def load_plugin(self, name, overlay, event_bus, config, game=None, status=None):
        dir_name = self._find_plugin_dir_by_name(name)
        if not dir_name:
            logger.warning(f"Plugin directory not found: {name}")
            return False
        plugin_path = os.path.join(self._plugin_dir, dir_name, "plugin.py")
        if not os.path.isfile(plugin_path):
            logger.warning(f"Plugin file not found: {name}")
            return False
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{dir_name}.plugin", plugin_path
            )
            if spec is None or spec.loader is None:
                return False
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for cls_name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Plugin) and obj is not Plugin:
                    instance = obj()
                    instance.on_load(overlay, event_bus, config, game, status)
                    self._plugins[instance.name] = instance
                    logger.info(f"Loaded plugin: {instance.name} v{instance.version}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}\n{traceback.format_exc()}")
            return False

    def _find_plugin_dir_by_name(self, name):
        return self._name_to_dir.get(name)

    def get_plugin(self, name):
        return self._plugins.get(name)

    def list_plugins(self):
        return list(self._plugins.keys())
