'''
Load tilemap files into objects.
Tilemap extension is .rcm
'''

import pygame
import ast
import copy
from pathlib import Path
from . import reusable, tileset

__version__ = "0.0.0 PT"

FORMAT = 0
'''The tilemap file format.'''

class Tilemap: 
    # a tilemap is a matrix of 'tiles' that makes the game map
    def __init__(
        self,
        name: str | None = None,
        module=None,
        tileset_module=None,
        sprite_definitions=None,
    ):
        if module is None:
            if name is None:
                raise ValueError("Tilemap requires a module or asset name")
            module = __import__(f"assets.tilemaps.{name}", fromlist=[name])
        self.module = module
        self.name = name or getattr(module, "name", "tilemap")
        self.tileset = tileset.Tileset(self.module.tileset, module=tileset_module)
        self.sprite_definitions = sprite_definitions or {}
        self.matrix = self.module.content
        self.entities = self.matrix[1]
        self.collision = self.matrix[0]
        self.layers = self.matrix[2:]
        self.dimensions = (len(self.entities[0]), len(self.entities))
        self.width = self.dimensions[0] * self.tileset.tile_size
        self.height = self.dimensions[1] * self.tileset.tile_size
        self.ground_tiles = pygame.Surface((self.dimensions[0]*self.tileset.tile_size, self.dimensions[1]*self.tileset.tile_size), pygame.SRCALPHA)
        self.priority_tiles = pygame.Surface((self.dimensions[0]*self.tileset.tile_size, self.dimensions[1]*self.tileset.tile_size), pygame.SRCALPHA)
        world_size = (self.width, self.height)
        self.geometry_tiles = pygame.Surface(world_size, pygame.SRCALPHA)
        self.filter_tiles = pygame.Surface(world_size, pygame.SRCALPHA)
        self.filter_tiles.fill((255, 255, 255, 255))
        self.shadow_sources = []
        self.shadow_source_groups = []
        self.shadow_grid = {}
        self.emission_sources = []
        self.included_tile_sprites = self.module.tile_sprites
        if isinstance(self.included_tile_sprites, str):
            self.included_tile_sprites = ast.literal_eval(self.included_tile_sprites)
        self.tile_sprites = self.entities.copy()
        self.render()

        for y, yc in enumerate(self.tile_sprites):
            for x, xc in enumerate(yc):
                if self.entities[y][x]:
                    sprite_name = self.included_tile_sprites[xc]
                    sprite_definition = self.sprite_definitions[sprite_name]
                    tile_sprite = (
                        sprite_definition(self)
                        if callable(sprite_definition)
                        else copy.copy(sprite_definition)
                    )
                    tile_sprite.grid_x = x
                    tile_sprite.grid_y = y
                    tile_sprite.x = x * self.tileset.tile_size + self.tileset.tile_size // 2
                    tile_sprite.y = (y + 1) * self.tileset.tile_size
                    tile_sprite.rect.midbottom = (tile_sprite.x, tile_sprite.y)
                    self.tile_sprites[y][x] = tile_sprite
                else:
                    self.tile_sprites[y][x] = None

            

    def render(self):
        for p in range(max(self.tileset.module.priority)+1):
            for z, zc in reversed(list(enumerate(self.layers))):
                for y, yc in enumerate(zc):
                    for x, xc in enumerate(yc):
                        tile = self.tileset.tile(xc)
                        if self.tileset.module.priority[self.layers[z][y][x]] == p == 0:
                            self.ground_tiles.blit(tile.surface, (x*self.tileset.tile_size, y*self.tileset.tile_size))
                        elif self.tileset.module.priority[self.layers[z][y][x]] == p:
                            self.priority_tiles.blit(tile.surface, (x*self.tileset.tile_size, y*self.tileset.tile_size))
                        if self.tileset.module.priority[self.layers[z][y][x]] == p:
                            tile_x = x * self.tileset.tile_size
                            tile_y = y * self.tileset.tile_size
                            self.geometry_tiles.blit(tile.geometry, (tile_x, tile_y))
                            self.filter_tiles.blit(tile.filter, (tile_x, tile_y))
                            tile_shadow_sources = []
                            for pixel_x, pixel_y, height, y_offset, depth, opacity in tile.shadow_pixels:
                                source = (
                                    tile_x + pixel_x,
                                    tile_y + pixel_y,
                                    height,
                                    y_offset,
                                    depth,
                                    opacity,
                                )
                                self.shadow_sources.append(source)
                                tile_shadow_sources.append(source)
                                cell = (source[0] // self.tileset.tile_size, source[1] // self.tileset.tile_size)
                                self.shadow_grid.setdefault(cell, []).append(source)
                            if tile_shadow_sources:
                                self.shadow_source_groups.append(tile_shadow_sources)
                            for pixel_x, pixel_y, red, green, blue, strength in tile.emission_pixels:
                                self.emission_sources.append({
                                    "x": tile_x + pixel_x + 0.5,
                                    "y": tile_y + pixel_y + 0.5,
                                    "color": (red, green, blue),
                                    "intensity": strength,
                                    "radius": self.tileset.tile_size * 1.25,
                                    "height": self.tileset.tile_size * 1.25,
                                    "casts_shadows": True
                                })
        return self

        
