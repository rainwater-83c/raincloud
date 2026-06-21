'''Reusable code for other scripts.'''

import logging
import coloredlogs
import pygame
import io
import importlib.util
import sys
import pathlib

__version__ = "0.0.0 PT"

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"reusable scripts loaded! version: {__version__}")

def bytes_to_image(bytes):
    image_stream = io.BytesIO(bytes)
    image_surface = pygame.image.load(image_stream)
    return image_surface

def path_to_module(path, format):
    module_name = path.stem
    file_path = path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    temp_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = temp_module
    spec.loader.exec_module(temp_module)
    if temp_module.format != format:
        logger.warning(f"The format for {path} is outdated! Proceed with caution.")
    return temp_module