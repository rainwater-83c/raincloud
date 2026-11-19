'''
Load tileset files into objects.
Tileset extension is .rct
'''

import pygame
import numpy as np
from pathlib import Path
import importlib.util
from . import reusable

__version__ = "0.0.0 PT"


FORMAT = 0
'''The tileset file format.'''

class Tileset:  
    # a tileset is an image with textures for tiles, also contains priority data.
    def __init__(self, name: str | None = None, module=None):
        if module is None:
            if name is None:
                raise ValueError("Tileset requires a module or asset name")
            module = __import__(f"assets.tilesets.{name}", fromlist=[name])
        self.module = module
        self.name = name or getattr(module, "name", "tileset")
        self.image = reusable.bytes_to_image(self.module.texture)
        image_size = self.image.get_size()
        self.geometry = reusable.module_image(
            self.module, "geometry", image_size, (128, 128, 0, 0)
        )
        self.emission = reusable.module_image(
            self.module, "emission", image_size, (0, 0, 0, 0)
        )
        self.filter = reusable.module_image(
            self.module, "filter", image_size, (255, 255, 255, 255)
        )
        self.tile_size = self.module.tile_size
        self.dimensions = (self.image.get_size()[0]/self.tile_size, self.image.get_size()[1]/self.tile_size)
        self._tile_cache = {}
    
    def tile(self, tile):
        if tile not in self._tile_cache:
            self._tile_cache[tile] = Tile(self, tile)
        return self._tile_cache[tile]



class Tile:
    def __init__(self, tileset, tile):
        self.tileset = tileset
        self.tile_index = tile
        self.size = self.tileset.tile_size
        self.column = tile%self.tileset.dimensions[0]
        self.row = tile//self.tileset.dimensions[0]
        self.rect = pygame.rect.Rect((self.column*self.size, self.row*self.size), (self.size, self.size))
        self.surface = self.tileset.image.subsurface(self.rect)
        self.geometry = self.tileset.geometry.subsurface(self.rect)
        self.emission = self.tileset.emission.subsurface(self.rect)
        self.filter = self.tileset.filter.subsurface(self.rect)
        self.shadow_pixels = []
        self.emission_pixels = []
        self.height = int(np.max(pygame.surfarray.array_red(self.geometry)))
        for y in range(self.size):
            for x in range(self.size):
                red, green, blue, alpha = self.geometry.get_at((x, y))
                if alpha and red >= 128 and blue > 0:
                    self.shadow_pixels.append((x, y, red - 128, 128 - green, blue, alpha / 255))

                red, green, blue, alpha = self.emission.get_at((x, y))
                if alpha and (red or green or blue):
                    self.emission_pixels.append((x, y, red, green, blue, alpha / 255))

    def split(self, geometry=None):
        textures = {}
        if geometry is None:
            geometry = self.geometry

        rgb = pygame.surfarray.array3d(self.surface)
        alpha = pygame.surfarray.array_alpha(self.surface)
        height = pygame.surfarray.array_red(geometry)

        for value in np.unique(height):
            mask = height == value

            surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA, 32)

            rgb_view = pygame.surfarray.pixels3d(surface)
            alpha_view = pygame.surfarray.pixels_alpha(surface)

            rgb_view[:] = rgb
            alpha_view[:] = np.where(mask, alpha, 0)

            del rgb_view, alpha_view  # release the surface pixel views
            textures[int(value)] = surface

        return textures

