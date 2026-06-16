'''
Load tileset files into objects.
Tileset extension is .rct
'''

import pygame
import logging
import coloredlogs
from pathlib import Path
import importlib.util
from scripts import reusable

__version__ = "0.0.0 PT"


logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"tileset script loaded! version: {__version__}")

FORMAT = 0
'''The tileset file format.'''

class Tileset:  
    # a tileset is an image with textures for tiles, also contains priority data.
    def __init__(self, name:str):
        self.name = name
        self.path = Path(f"assets/tilesets/{name}.py").absolute()
        self.module = reusable.path_to_module(self.path, FORMAT)
        self.image = reusable.bytes_to_image(self.module.content)
        self.tile_size = self.module.tile_size
        self.dimensions = (self.image.get_size()[0]/self.tile_size, self.image.get_size()[1]/self.tile_size)
        
        
    
    def tile(self, tile):
        return Tile(self, tile)

class Tile:
    def __init__(self, tileset, tile):
        self.tileset = tileset
        self.tile_index = tile
        self.size = self.tileset.tile_size
        self.column = tile%self.tileset.dimensions[0]
        self.row = tile//self.tileset.dimensions[0]
        self.rect = pygame.rect.Rect((self.column*self.size, self.row*self.size), (self.size, self.size))
        self.surface = self.tileset.image.subsurface(self.rect)

