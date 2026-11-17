"""Load required game assets and behavior separately from optional mods."""

import hashlib
import importlib.util
import sys
from pathlib import Path


class CoreGameLoader:
    def __init__(self, project_root, asset_paths):
        self.project_root = Path(project_root).resolve()
        self.asset_paths = dict(asset_paths)
        self.assets = {}
        self.config = None

    @classmethod
    def from_project(cls, project_root, config_filename="config.py"):
        project_root = Path(project_root).resolve()
        config_path = project_root / config_filename
        if not config_path.is_file():
            raise FileNotFoundError(f"Game config does not exist: {config_path}")

        module_name = f"_raincloud_config_{hashlib.sha1(str(config_path).encode('utf-8')).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, config_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load game config from {config_path}")

        config = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = config
        try:
            spec.loader.exec_module(config)
        except Exception:
            sys.modules.pop(module_name, None)
            raise

        asset_paths = getattr(config, "ASSET_PATHS", None)
        if not isinstance(asset_paths, dict):
            raise ValueError(f"{config_path} must define ASSET_PATHS as a dictionary")

        loader = cls(project_root, asset_paths)
        loader.config = config
        return loader

    def load(self):
        for asset_name, asset_path in self.asset_paths.items():
            if asset_path is None:
                continue

            path = Path(asset_path)
            if not path.is_absolute():
                path = self.project_root / path
            path = path.resolve()
            if not path.is_file():
                raise FileNotFoundError(
                    f"Configured core asset '{asset_name}' does not exist: {path}"
                )

            module_digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
            module_name = f"_raincloud_core_{asset_name}_{module_digest}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load core asset '{asset_name}' from {path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(module_name, None)
                raise
            self.assets[asset_name] = module

        return self

    def install(self, app):
        app.core_assets = self.assets

        credits = self.assets.get("credits")
        app.credits = getattr(credits, "CREDITS", {})

        keybinds = self.assets.get("keybinds")
        if keybinds is not None:
            app.keybinds = getattr(keybinds, "KEYBINDS", app.keybinds)
            app.gamepad_keybinds = getattr(
                keybinds,
                "GAMEPAD_KEYBINDS",
                app.gamepad_keybinds,
            )

        events = self.assets.get("events")
        if events is not None:
            app.events.update({
                event_type: self._event_callback(app, callback)
                for event_type, callback in getattr(events, "EVENTS", {}).items()
            })
            app.keys.update({
                action: self._action_callback(app, callback)
                for action, callback in getattr(events, "KEYS", {}).items()
            })
            app.oncekeys.update({
                action: self._action_callback(app, callback)
                for action, callback in getattr(events, "ONCE_KEYS", {}).items()
            })

        menus = self.assets.get("menus")
        app.menu_definitions = getattr(menus, "MENUS", {})

        sprites = self.assets.get("sprites")
        app.sprite_definitions = getattr(sprites, "sprites", {})

        core_game = self.assets.get("core_game")
        register = getattr(core_game, "register", None)
        if register is not None:
            register(app, self.assets)

        return app

    @staticmethod
    def _event_callback(app, callback):
        return lambda event: callback(app, event)

    @staticmethod
    def _action_callback(app, callback):
        return lambda: callback(app)