'''
The main script to be packaged.
'''

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
from logging.handlers import RotatingFileHandler
import logging
import argparse
import coloredlogs
import scripts
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
logging.basicConfig(filename="logs/latest.log")

if __name__ == "__main__":
    logger.debug(f"main script ran! version: {__version__}")
    app = app.App(tilemap.Tilemap('test'))  # make a new app object
    app.run()  # run the app