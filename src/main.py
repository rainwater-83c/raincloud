'''The main script to be packaged.'''

import sys

#sys.path.append("modules.rca")
#sys.path.append("modules")

import os
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
scripts_path = os.path.join(BASE_DIR, "scripts.rcs")
sys.path.insert(0, scripts_path)
assets_path = os.path.join(BASE_DIR, "assets.rca")
sys.path.insert(0, assets_path)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
from logging.handlers import RotatingFileHandler
import logging
import argparse
import coloredlogs
import winreg
import assets
import pydualsense
import scripts

from assets import *
from scripts import * # load all of the scripts

# importing something means taking a class, function, or variable from a file and putting it in this program
# pygame is a module, which is in a different location

__version__ = "0.0.0 PT"
# PT = Prototype version; Still in development.
# A = Alpha version; Internal testing.
# B = Beta version; Playerbase testing.

#os.remove("logs/latest.log")

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
#logging.basicConfig(filename="logs/latest.log")

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcs") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudScript")

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rca") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudAssets")

#with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcm") as key:
#    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudMod")


if __name__ == "__main__":
    logger.debug(f"main script ran! version: {__version__}")
    app = app.App(tilemap.Tilemap('main'))  # make a new app object
    modloader = modloader.Modloader(app) # init the modloader
    modloader.inject() # inject the mods into the app object
    app.run()  # run the app
    del app
    os._exit(0)
