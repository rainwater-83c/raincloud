'''
Load tilemap files into objects.
Tilemap extension is .rcm
'''

import pygame
import ast
import copy
import numpy as np
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
        self.matrix = self.module.tilemap
        self.entities = self.matrix[1]
        self.collision = getattr(self.module, "collision", self.matrix[0])
        self.layers = self.matrix[2:]
        self.height_map = getattr(self.module, "height", None)
        self.displacement_map = getattr(self.module, "displacement", None)
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
        self.height_layers = {}
        self.included_tile_sprites = self.module.tile_sprites
        if isinstance(self.included_tile_sprites, str):
            self.included_tile_sprites = ast.literal_eval(self.included_tile_sprites)
        self.tile_sprites = self.entities.copy()
        self.render2()

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

    def render2(self):
        for z, zc in reversed(list(enumerate(self.layers))):
            for y, yc in enumerate(zc):
                for x, xc in enumerate(yc):
                    tile = self.tileset.tile(xc)
                    tile_geometry = self._adjusted_tile_geometry(tile, z, y, x)
                    tile_layers = tile.split(tile_geometry)

                    for height, surface in tile_layers.items():
                        if height not in self.height_layers:
                            self.height_layers[height] = pygame.Surface(
                                (self.width, self.height),
                                pygame.SRCALPHA
                            )

                        self.height_layers[height].blit(
                            surface,
                            (x * self.tileset.tile_size, y * self.tileset.tile_size)
                        )


                        tile_x = x * self.tileset.tile_size
                        tile_y = y * self.tileset.tile_size
                        self.geometry_tiles.blit(tile_geometry, (tile_x, tile_y))
                        self.filter_tiles.blit(tile.filter, (tile_x, tile_y))
                        tile_shadow_sources = []
                        for pixel_y in range(tile.size):
                            for pixel_x in range(tile.size):
                                red, green, blue, alpha = tile_geometry.get_at((pixel_x, pixel_y))
                                if not alpha or red < 128 or blue == 0:
                                    continue
                                source = (
                                    tile_x + pixel_x,
                                    tile_y + pixel_y,
                                    red - 128,
                                    128 - green,
                                    blue,
                                    alpha / 255,
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

    def _adjusted_tile_geometry(self, tile, layer_index, y, x):
        height_units = self._tile_attribute_value(
            self.height_map,
            layer_index,
            y,
            x,
        )
        displacement_units = self._tile_attribute_value(
            self.displacement_map,
            layer_index,
            y,
            x,
        )
        height_offset = round(height_units * self.tileset.tile_size)
        displacement_offset = round(displacement_units * self.tileset.tile_size)
        if not height_offset and not displacement_offset:
            return tile.geometry

        geometry = tile.geometry.copy()
        rgb = pygame.surfarray.pixels3d(geometry)
        rgb[:, :, 0] = np.clip(
            rgb[:, :, 0].astype(np.int16) + height_offset,
            0,
            255,
        ).astype(np.uint8)
        rgb[:, :, 1] = np.clip(
            rgb[:, :, 1].astype(np.int16) - displacement_offset,
            0,
            255,
        ).astype(np.uint8)
        del rgb
        return geometry

    def _collision_tiles_at(self, grid_x, grid_y):
        collision_map = self.collision
        if not collision_map or not collision_map[0]:
            return [
                (layer_index, layer[grid_y][grid_x])
                for layer_index, layer in enumerate(self.layers)
                if grid_y < len(layer) and grid_x < len(layer[grid_y])
            ]

        marked_tiles = []
        if isinstance(collision_map[0][0], (list, tuple)):
            layer_offset = len(self.layers) - len(collision_map)
            for collision_index, collision_layer in enumerate(collision_map):
                layer_index = collision_index + layer_offset
                if (
                    not 0 <= layer_index < len(self.layers)
                    or grid_y >= len(collision_layer)
                    or grid_x >= len(collision_layer[grid_y])
                    or not collision_layer[grid_y][grid_x]
                ):
                    continue
                layer = self.layers[layer_index]
                if grid_y < len(layer) and grid_x < len(layer[grid_y]):
                    marked_tiles.append((layer_index, layer[grid_y][grid_x]))
            return marked_tiles

        if (
            grid_y >= len(collision_map)
            or grid_x >= len(collision_map[grid_y])
            or not collision_map[grid_y][grid_x]
        ):
            return []
        return [
            (layer_index, layer[grid_y][grid_x])
            for layer_index, layer in enumerate(self.layers)
            if grid_y < len(layer) and grid_x < len(layer[grid_y])
        ]

    def _projected_collision_surfaces_at(self, grid_x, grid_y, raised_only=False):
        tile_size = self.tileset.tile_size
        row_reach = (128 + tile_size - 1) // tile_size + 1
        source_rows = range(
            max(0, grid_y - row_reach),
            min(self.dimensions[1], grid_y + row_reach + 1),
        )
        pixel_rows = np.arange(tile_size)[None, :]
        direct_surfaces = []
        projected_surfaces = []

        for source_y in source_rows:
            for layer_index, tile_index in self._collision_tiles_at(grid_x, source_y):
                tile = self.tileset.tile(tile_index)
                geometry = self._adjusted_tile_geometry(
                    tile,
                    layer_index,
                    source_y,
                    grid_x,
                )
                alpha = pygame.surfarray.array_alpha(geometry) > 0
                red = pygame.surfarray.array_red(geometry).astype(np.int16)
                green = pygame.surfarray.array_green(geometry).astype(np.int16)
                pixel_displacement = 128 - green
                projected_y = source_y * tile_size + pixel_rows + pixel_displacement
                projected_pixels = alpha & (projected_y // tile_size == grid_y)
                if raised_only:
                    projected_pixels &= red > 128
                for pixel_x, pixel_y in np.argwhere(projected_pixels):
                    surface = (
                        int(red[pixel_x, pixel_y]),
                        int(projected_y[pixel_x, pixel_y] - (grid_y + 1) * tile_size),
                        int(green[pixel_x, pixel_y]),
                    )
                    if source_y == grid_y:
                        direct_surfaces.append(surface)
                    else:
                        projected_surfaces.append(surface)
        return direct_surfaces or projected_surfaces

    def minimum_displacement_at(self, grid_x, grid_y):
        surfaces = self._projected_collision_surfaces_at(
            grid_x,
            grid_y,
            raised_only=True,
        )
        if not surfaces:
            return 0
        highest_surface = max(height for height, _, _ in surfaces)
        return min(
            green - 128
            for height, _, green in surfaces
            if height == highest_surface
        )

    def tile_height_at(self, grid_x, grid_y, reference_height):
        heights = []
        for layer_index, layer in enumerate(self.layers):
            if grid_y >= len(layer) or grid_x >= len(layer[grid_y]):
                continue
            tile = self.tileset.tile(layer[grid_y][grid_x])
            geometry = tile.geometry
            alpha = pygame.surfarray.array_alpha(geometry)
            red = pygame.surfarray.array_red(geometry)
            active_heights = red[alpha > 0]
            heights.append(
                int(active_heights.max()) if active_heights.size else tile.height
            )
        if not heights:
            return reference_height
        return min(heights, key=lambda height: abs(reference_height - height))

    def tile_height_offset_at(self, grid_x, grid_y):
        if self.height_map is None:
            return 0
        height_offsets = [
            self._tile_attribute_value(
                self.height_map,
                layer_index,
                grid_y,
                grid_x,
            )
            for layer_index, layer in enumerate(self.layers)
            if grid_y < len(layer) and grid_x < len(layer[grid_y])
        ]
        return round(max(height_offsets, default=0) * self.tileset.tile_size)

    def _tile_attribute_value(self, attribute_map, layer_index, y, x):
        if attribute_map is None:
            return 0
        if isinstance(attribute_map, str):
            attribute_map = ast.literal_eval(attribute_map)
        if isinstance(attribute_map, (int, float)):
            return float(attribute_map)
        if not attribute_map:
            return 0

        first = attribute_map[0]
        if first and isinstance(first[0], (list, tuple)):
            if len(attribute_map) == len(self.layers):
                plane = attribute_map[layer_index]
            elif len(attribute_map) == len(self.matrix):
                plane = attribute_map[layer_index + 2]
            else:
                raise ValueError(
                    "3D tilemap height and displacement maps must match visual "
                    "layers or the full tilemap stack"
                )
            return float(plane[y][x])

        return float(attribute_map[y][x])

            

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

        
