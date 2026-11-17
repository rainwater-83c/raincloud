'''The engine entry point for the built-in game project.'''

from pathlib import Path
import sys

from raincloud.scripts.app import App
from raincloud.scripts.coreloader import CoreGameLoader
from raincloud.scripts.modloader import Modloader
from raincloud.scripts.tilemap import Tilemap

__version__ = "0.0.0 PT"
# PT = Prototype version; Still in development.
# A = Alpha version; Internal testing.
# B = Beta version; Playerbase testing.

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcs") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudScript")

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rca") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudAssets")

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcm") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudMod")


def main():
    project_root = Path(sys.argv[0]).resolve().parent
    core_loader = CoreGameLoader.from_project(project_root).load()
    core_assets = core_loader.assets
    tilemap = Tilemap(
        module=core_assets["tilemap"],
        tileset_module=core_assets["tileset"],
        sprite_definitions=core_assets["sprites"].sprites,
    )
    app = App(tilemap, core_assets, core_loader.config)
    core_loader.install(app)

    modloader = Modloader(app)
    modloader.inject()
    app.run()


if __name__ == "__main__":
    main()
