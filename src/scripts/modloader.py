'''Built-in modloader. Mod extension is .rcm'''

from scripts.app import App
import mods

loaded_mods = {
    name: getattr(mods, name)
    for name in mods.__all__
}

class Modloader:
    def __init__(self, app: App):
        self.events = {}
        self.keys = {}
        self.oncekeys = {}
        self.app = app

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
        for mod in loaded_mods.values():
            try:
                mod.Mod(self)
            except Exception as e:
                print(f"mod error: {e}")
        self.app.events = self.events
        self.app.keys = self.keys
        self.app.oncekeys = self.oncekeys
