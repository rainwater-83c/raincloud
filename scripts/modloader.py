'''Loader for optional game-project plugins.'''

import hashlib
import importlib.util
import sys
from pathlib import Path

from raincloud.scripts.app import App

class Modloader:
    def __init__(self, app: App, plugin_dir=None):
        self.events = {}
        self.keys = {}
        self.oncekeys = {}
        self.app = app
        self.plugin_dir = Path(plugin_dir).resolve() if plugin_dir else None

    def event(self, event):
        def decorator(func):
            self.events[event] = func
            return func
        return decorator
    
    def key(self, key):
        def decorator(func):
            self.keys[key] = func
            return func
        return decorator
    
    def oncekey(self, key):
        def decorator(func):
            self.oncekeys[key] = func
            return func
        return decorator
    
    def inject(self):
        if self.plugin_dir and self.plugin_dir.is_dir():
            for path in sorted(self.plugin_dir.glob("*.py")):
                if path.name.startswith("_"):
                    continue
                digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:10]
                module_name = f"_raincloud_plugin_{path.stem}_{digest}"
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load plugin: {path}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                register = getattr(module, "register", None)
                if register is not None:
                    register(self)
                else:
                    plugin_class = getattr(module, "Plugin", None)
                    if plugin_class is not None:
                        plugin_class(self)
        self.app.events.update(self.events)
        self.app.keys.update(self.keys)
        self.app.oncekeys.update(self.oncekeys)
