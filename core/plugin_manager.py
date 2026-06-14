import importlib.util
import inspect
import os
import re
import sys
import logging
import traceback

from .plugin_base import Plugin
from .plugin_api import _collect_event_handlers, _find_post_load

logger = logging.getLogger(__name__)


def _wrap_new_style(cls):
    meta = cls._plugin_meta
    has_create = callable(getattr(cls, "create", None))
    settings_tab_name = meta.get("settings_tab")

    class Wrapper(Plugin):
        name = meta["name"]
        version = meta["version"]
        description = meta["description"]
        window_position = meta["position"]
        window_width = meta["width"]
        window_height = meta["height"]
        window_max_height = meta["max_height"]
        window_offset_x = meta["offset_x"]
        journal_events = meta["journal_events"]
        status_events = meta["status_events"]
        _settings_tab = settings_tab_name
        _settings_only = not has_create
        _relative_to = meta.get("relative_to")
        _relative_pos = meta.get("relative_pos", "bottom")

        def __init__(self):
            self._user_cls = cls()
            self._event_handlers = _collect_event_handlers(cls)
            self._post_load_name = _find_post_load(cls)
            self._dynamic = meta["dynamic"]

        def create_widgets(self, parent):
            if not has_create:
                return
            ctx = self._create_context()
            self._user_cls.create(ctx)

        def on_event(self, event, data):
            ctx = self._create_context(event)
            handlers = self._event_handlers.get(event, [])
            for method_name in handlers:
                method = getattr(self._user_cls, method_name)
                try:
                    method(ctx, data)
                except Exception as e:
                    logger.error(
                        f"Error in handler {method_name} for {event}: {e}\n"
                        f"{traceback.format_exc()}"
                    )

        def post_load(self):
            ctx = self._create_context()
            if self._post_load_name:
                method = getattr(self._user_cls, self._post_load_name)
                try:
                    method(ctx)
                except Exception as e:
                    logger.error(f"Error in post_load: {e}\n{traceback.format_exc()}")
            if self._dynamic:
                dynamic = self.pcfg.get("dynamic", False)
                if dynamic:
                    self.set_visible(False)

        def build_settings(self, parent, overlay, config):
            if hasattr(self._user_cls, "build_settings"):
                try:
                    self._user_cls.build_settings(parent, overlay, config)
                except Exception as e:
                    logger.error(f"Error building settings: {e}\n{traceback.format_exc()}")

        def on_unload(self):
            self._user_cls.__dict__.pop("overlay", None)
            if not has_create:
                self._cleanup_subscriptions()
            else:
                super().on_unload()

    return Wrapper


def _instantiate_new_style(cls):
    return _wrap_new_style(cls)()


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
                # Try old-style: name = "..."
                m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', src)
                if m:
                    self._name_to_dir[m.group(1)] = entry
                    continue
                # Try new-style: @plugin(name="...")
                m = re.search(r'@plugin\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', src)
                if m:
                    self._name_to_dir[m.group(1)] = entry
            except OSError:
                continue

    def _load_module(self, module_path, module_name, overlay, event_bus, config, game, status):
        """Load a plugin from a module file. Returns (name, instance) or (None, None)."""
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            return None, None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for cls_name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj is not Plugin:
                instance = obj()
                name = instance.name
                plugin_config = config.plugin_config(name)
                if not plugin_config.get("enabled", True):
                    logger.info(f"Plugin disabled: {name}")
                    return None, None
                try:
                    instance.on_load(overlay, event_bus, config, game, status)
                except Exception as e:
                    logger.error(f"Plugin {name} failed to load: {e}\n{traceback.format_exc()}")
                    self._cleanup_failed_plugin(instance, overlay)
                    return None, None
                self._plugins[name] = instance
                logger.info(f"Loaded plugin: {name} v{instance.version}")
                return name, instance
            if hasattr(obj, "_plugin_meta"):
                instance = _instantiate_new_style(obj)
                meta = obj._plugin_meta
                name = meta["name"]
                plugin_config = config.plugin_config(name)
                if not plugin_config.get("enabled", True):
                    logger.info(f"Plugin disabled: {name}")
                    return None, None
                try:
                    instance.on_load(overlay, event_bus, config, game, status)
                except Exception as e:
                    logger.error(f"Plugin {name} failed to load: {e}\n{traceback.format_exc()}")
                    self._cleanup_failed_plugin(instance, overlay)
                    return None, None
                self._plugins[name] = instance
                logger.info(f"Loaded plugin: {name} v{meta['version']}")
                return name, instance
        return None, None

    def _cleanup_failed_plugin(self, instance, overlay):
        """Clean up partial state from a plugin that failed during on_load."""
        try:
            instance._cleanup_subscriptions()
        except Exception:
            pass
        try:
            if hasattr(instance, "win"):
                overlay.remove_plugin_window(instance.name)
                overlay.remove_plugin_container(instance.name)
        except Exception:
            pass

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
                self._load_module(
                    plugin_file, f"plugins.{entry}.plugin",
                    overlay, event_bus, config, game, status,
                )
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
        if overlay and hasattr(plugin, "win"):
            overlay.remove_plugin_container(name)
            overlay.remove_plugin_window(name)
        return True

    def unload_all(self, overlay=None):
        for name in list(self._plugins.keys()):
            self.unload_plugin(name, overlay)

    def load_plugin(self, name, overlay, event_bus, config, game=None, status=None):
        dir_name = self._name_to_dir.get(name)
        if not dir_name:
            logger.warning(f"Plugin directory not found: {name}")
            return False
        plugin_path = os.path.join(self._plugin_dir, dir_name, "plugin.py")
        if not os.path.isfile(plugin_path):
            logger.warning(f"Plugin file not found: {name}")
            return False
        try:
            loaded_name, _ = self._load_module(
                plugin_path, f"plugins.{dir_name}.plugin",
                overlay, event_bus, config, game, status,
            )
            return loaded_name is not None
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}\n{traceback.format_exc()}")
            return False

    def get_plugin(self, name):
        return self._plugins.get(name)

    def get_settings_tabs(self):
        """Return list of (tab_name, plugin_instance) for plugins with settings tabs."""
        tabs = []
        for name, plugin in self._plugins.items():
            tab_name = getattr(plugin, "_settings_tab", None)
            if tab_name and hasattr(plugin, "build_settings"):
                tabs.append((tab_name, plugin))
        return tabs

    def list_plugins(self):
        return list(self._plugins.keys())

    def apply_profile(self, config, overlay):
        """Apply the active profile layout to all loaded plugins."""
        active = config.get("active_profile", default="")
        if not active:
            return
        profiles = config.get("profiles", default={})
        layout = profiles.get(active)
        if not layout:
            return
        for pname, data in layout.items():
            pcfg = config.data.setdefault("plugins", {}).setdefault(pname, {})
            pcfg.update(data)
            plugin_inst = self._plugins.get(pname)
            if not plugin_inst:
                continue
            if hasattr(plugin_inst, "win") and hasattr(plugin_inst.win, "set_locked"):
                plugin_inst.win.set_locked(data.get("locked", False))
            if "window_position" in data and plugin_inst:
                overlay.reposition_plugin(pname, data["window_position"])
        config.save()
        logger.info(f"Applied profile: {active}")

    def apply_profile_config(self, config):
        """Write active profile enabled/disabled states to plugin configs.
        Call this BEFORE load_all so plugins load with correct enabled states."""
        active = config.get("active_profile", default="")
        if not active:
            return
        profiles = config.get("profiles", default={})
        layout = profiles.get(active)
        if not layout:
            return
        for pname, data in layout.items():
            pcfg = config.data.setdefault("plugins", {}).setdefault(pname, {})
            pcfg.update(data)
        config.save()
