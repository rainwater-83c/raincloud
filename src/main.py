'''The main script to be packaged.'''

import sys
sys.path.append("scripts.rcs")
sys.path.append("modules.rca")
sys.path.append("modules")
sys.path.append("assets.rca")
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
from logging.handlers import RotatingFileHandler
import logging
import argparse
import coloredlogs
import winreg
import scripts

from scripts import * # load all of the scripts

with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcs") as key:
    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudScript")

with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rca") as key:
    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudAssets")

with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".rcm") as key:
    winreg.SetValue(key, "", winreg.REG_SZ, "RaincloudMod")

# importing something means taking a class, function, or variable from a file and putting it in this program
# pygame is a module, which is in a different location

__version__ = "0.0.0 PT"
# PT = Prototype version; Still in development.
# A = Alpha version; Internal testing.
# B = Beta version; Playerbase testing.

#os.remove("logs/latest.log")

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")

if __name__ == "__main__":
    logger.debug(f"main script ran! version: {__version__}")
    app = app.App(tilemap.Tilemap('test'))  # make a new app object
    modloader = modloader.Modloader(app)
    modloader.inject()
    app.run()  # run the app