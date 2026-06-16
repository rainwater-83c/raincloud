'''
Load tilemap files into objects.
Tilemap extension is .rcm
'''

import pygame
import logging
import coloredlogs
from pathlib import Path
from scripts import reusable, tileset

__version__ = "0.0.0 PT"

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"tilemap script loaded! version: {__version__}")

FORMAT = 0
'''The tilemap file format.'''

class Tilemap: 
    # a tilemap is a matrix of 'tiles' that makes the game map
    def __init__(self, name:str):
        self.name = name
        self.path = Path(f"assets/tilemaps/{name}.py").absolute()
        self.module = reusable.path_to_module(self.path, FORMAT)
        self.tileset = tileset.Tileset(self.module.tileset)
        self.matrix = self.module.content
        self.entities = self.matrix[0]
        self.collision = self.matrix[1]
        self.layers = self.matrix[2:]
        self.dimensions = (len(self.entities[0]), len(self.entities))
        self.width = self.dimensions[0] * self.tileset.tile_size
        self.height = self.dimensions[1] * self.tileset.tile_size
        self.ground_tiles = pygame.Surface((self.dimensions[0]*self.tileset.tile_size, self.dimensions[1]*self.tileset.tile_size), pygame.SRCALPHA)
        self.priority_tiles = pygame.Surface((self.dimensions[0]*self.tileset.tile_size, self.dimensions[1]*self.tileset.tile_size), pygame.SRCALPHA)
        self.render()

    def render(self):
        for p in range(max(self.tileset.module.priority)+1):
            for z, zc in enumerate(self.layers):
                for y, yc in enumerate(zc):
                    for x, xc in enumerate(yc):
                        tile = self.tileset.tile(xc)
                        if self.tileset.module.priority[self.layers[z][y][x]] == p == 0:
                            self.ground_tiles.blit(tile.surface, (x*self.tileset.tile_size, y*self.tileset.tile_size))
                        elif self.tileset.module.priority[self.layers[z][y][x]] == p:
                            self.priority_tiles.blit(tile.surface, (x*self.tileset.tile_size, y*self.tileset.tile_size))
        return self

        
