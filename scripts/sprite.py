'''
Load sprite files into objects.
Spritesheet extension is .rcs
'''
import numpy as np
import pygame
from pathlib import Path
from . import reusable, tilemap, tileset

__version__ = "0.0.0 PT"

FORMAT = 0
'''The sprite file format.'''

class Spritesheet:
    def __init__(self, name: str, frames: int):
        self.name = name
        self.frames = frames
        self.module = __import__(f"assets.spritesheets.{name}", fromlist=[name])
        texture_bytes = self.module.texture
        self.image = reusable.bytes_to_image(texture_bytes)
        image_size = self.image.get_size()
        self.geometry = reusable.module_image(
            self.module, "geometry", image_size, (128, 128, 0, 0)
        )
        self._split_cache = {}
        self.emission = reusable.module_image(
            self.module, "emission", image_size, (0, 0, 0, 0)
        )
        if getattr(self.module, "filter", None) is None:
            self.filter = pygame.Surface(image_size, pygame.SRCALPHA)
            for y in range(image_size[1]):
                for x in range(image_size[0]):
                    alpha = self.image.get_at((x, y)).a
                    if alpha:
                        self.filter.set_at((x, y), (255, 255, 255, alpha))
        else:
            self.filter = reusable.module_image(
                self.module, "filter", image_size, (255, 255, 255, 255)
            )

    def surface(self, direction: int, frame: int):
        self.rect = pygame.rect.Rect(((frame/4)*self.image.get_width(), (direction/4)*self.image.get_height()), (self.image.get_width()/4, self.image.get_height()/4))
        return self.image.subsurface(self.rect)

    def map_surface(self, image, direction: int, frame: int):
        rect = pygame.rect.Rect(
            ((frame / 4) * image.get_width(), (direction / 4) * image.get_height()),
            (image.get_width() / 4, image.get_height() / 4)
        )
        return image.subsurface(rect)

    def geometry_surface(self, direction: int, frame: int):
        return self.map_surface(self.geometry, direction, frame)

    def emission_surface(self, direction: int, frame: int):
        return self.map_surface(self.emission, direction, frame)

    def filter_surface(self, direction: int, frame: int):
        return self.map_surface(self.filter, direction, frame)

    def split_surfaces(self, direction: int, frame: int):
        key = (direction, frame)
        if key not in self._split_cache:
            image = self.map_surface(self.image, direction, frame)
            geometry = self.geometry_surface(direction, frame)
            rgb = pygame.surfarray.array3d(image)
            alpha = pygame.surfarray.array_alpha(image)
            height = pygame.surfarray.array_red(geometry)
            textures = {}

            for value in np.unique(height):
                mask = height == value
                surface = pygame.Surface(image.get_size(), pygame.SRCALPHA, 32)
                rgb_view = pygame.surfarray.pixels3d(surface)
                alpha_view = pygame.surfarray.pixels_alpha(surface)
                rgb_view[:] = rgb
                alpha_view[:] = np.where(mask, alpha, 0)
                del rgb_view, alpha_view
                textures[int(value)] = surface

            self._split_cache[key] = textures
        return self._split_cache[key]

class Sprite(pygame.sprite.Sprite):
    '''An event or object that moves or is interactable. Also known as an entity.'''

    def __init__(self, spritesheet: Spritesheet, name: str, x: int, y: int, tilemap, direction: int=0, speed: int=1.25, health: int=3):
        super().__init__()
        self.path = name
        self.spritesheet = spritesheet
        self.tilemap = tilemap
        self.health = health
        self.grid_x = x
        self.grid_y = y
        self.target_x = None
        self.target_y = None
        self.height = 128
        self.displacement = 0
        self.step_height = 16
        minimum_displacement = getattr(self.tilemap, "minimum_displacement_at", None)
        self._tile_min_displacement = (
            minimum_displacement(x, y) if minimum_displacement is not None else 0
        )
        tile_size = self.tilemap.tileset.tile_size

        self.x = self.grid_x * tile_size + tile_size // 2
        self.y = (self.grid_y + 1) * tile_size
        self.direction = direction
        self.frame = 0
        self.speed = speed
        self.frame = 0
        self.dx = 0
        self.dy = 0
        self.state = 'idle'
        self.surface = self.spritesheet.surface(self.direction, self.frame)
        self.geometry = self.spritesheet.geometry_surface(self.direction, self.frame)
        self.rect = self.surface.get_rect()
        self.moving = False
        self.buffered_input = None
        self.anim_timer = 0
        self.move_speed = 0
        self.movenext = False
        self.nextprogress = 0
        self.walk_cycle = 0
        self.anim_timer = 0

    def split(self):
        return self.spritesheet.split_surfaces(self.direction, self.frame)

    def update(self, dt: float, speed: float = None):
        if self.moving:
            dx = self.target_x - self.start_x
            dy = self.target_y - self.start_y
            
            if speed is None:
                speed = self.move_speed
            self.move_timer += dt
            progress = self.move_timer * speed

            if progress >= 1:
                self.x = self.target_x
                self.y = self.target_y

                self.move_timer = 0
                self.moving = False
            else:
                self.x = self.start_x + dx * progress
                self.y = self.start_y + dy * progress

                # Animation while moving
            self.anim_timer += dt
            self.frame = int(self.anim_timer * speed*2) % 4

        else:
            self.move_speed = 0

            # Standing frame
            self.anim_timer = 0
            self.frame = 0

        self.surface = self.spritesheet.surface(self.direction, self.frame)
        self.geometry = self.spritesheet.geometry_surface(self.direction, self.frame)
        

    def move(self, dx:int, dy:int, speed=1):
        directions = {
            (0, 1): 0,
            (-1, 0): 1,
            (1, 0): 2,
            (0, -1): 3,
        }
        direction = directions.get((dx, dy))
        if direction is None:
            if dx == 0 and dy == 0:
                self.movenext = False
                self.buffered_input = None
            return

        if self.moving:
            self.movenext = True
            if direction != self.direction:
                self.buffered_input = (dx, dy)
            return

        self.direction = direction
        self.movenext = True
        target_x = self.grid_x + dx
        target_y = self.grid_y + dy
        map_width, map_height = self.tilemap.dimensions
        if not (0 <= target_y < map_height and 0 <= target_x < map_width):
            return

        minimum_displacement = getattr(self.tilemap, "minimum_displacement_at", None)
        target_min_displacement = (
            minimum_displacement(target_x, target_y)
            if minimum_displacement is not None
            else self._tile_min_displacement
        )
        #print(self._tile_min_displacement, target_min_displacement)
        target_displacement = (
            self.displacement + target_min_displacement - self._tile_min_displacement
        )
        collision_height = self._collision_height_at(
            target_x,
            target_y,
            target_displacement,
        )
        if collision_height is None:
            target_height = self._tile_height_at(target_x, target_y)
            height_offset_at = getattr(self.tilemap, "tile_height_offset_at", None)
            if height_offset_at is not None:
                target_height += height_offset_at(target_x, target_y)
        else:
            target_height = collision_height

        if abs(self.height - target_height) > self.step_height:
            return

        self.move_timer = 0
        self.start_x = self.x
        self.start_y = self.y
        self.grid_x = target_x
        self.grid_y = target_y
        self.height = target_height
        self.displacement = target_displacement
        self._tile_min_displacement = target_min_displacement

        tile_size = self.tilemap.tileset.tile_size
        self.target_x = self.grid_x * tile_size + tile_size // 2
        self.target_y = (self.grid_y + 1) * tile_size
        self.move_speed = speed
        self.moving = True

    def _collision_height_at(self, grid_x, grid_y, player_displacement=0):
        projected_surfaces_at = getattr(
            self.tilemap,
            "_projected_collision_surfaces_at",
            None,
        )
        if projected_surfaces_at is not None:
            surfaces = projected_surfaces_at(grid_x, grid_y)
            return max((surface[0] for surface in surfaces), default=None)

        collision_map = self.tilemap.collision
        if not collision_map or not collision_map[0]:
            return None

        marked_tile_indices = []
        if isinstance(collision_map[0][0], (list, tuple)):
            layer_offset = len(self.tilemap.layers) - len(collision_map)
            for collision_index, collision_layer in enumerate(collision_map):
                if (
                    grid_y >= len(collision_layer)
                    or grid_x >= len(collision_layer[grid_y])
                    or not collision_layer[grid_y][grid_x]
                ):
                    continue

                tile_layer_index = collision_index + layer_offset
                if not 0 <= tile_layer_index < len(self.tilemap.layers):
                    return self.height + self.step_height + 1
                tile_layer = self.tilemap.layers[tile_layer_index]
                if grid_y >= len(tile_layer) or grid_x >= len(tile_layer[grid_y]):
                    return self.height + self.step_height + 1
                marked_tile_indices.append((tile_layer_index, tile_layer[grid_y][grid_x]))
        else:
            if (
                grid_y >= len(collision_map)
                or grid_x >= len(collision_map[grid_y])
                or not collision_map[grid_y][grid_x]
            ):
                return None
            marked_tile_indices.extend(
                (layer_index, layer[grid_y][grid_x])
                for layer_index, layer in enumerate(self.tilemap.layers)
                if grid_y < len(layer) and grid_x < len(layer[grid_y])
            )

        if not marked_tile_indices:
            return None

        found_geometry = False
        collision_heights = []
        for layer_index, tile_index in marked_tile_indices:
            tile = self.tilemap.tileset.tile(tile_index)
            geometry_for_tile = getattr(self.tilemap, "_adjusted_tile_geometry", None)
            geometry = (
                geometry_for_tile(tile, layer_index, grid_y, grid_x)
                if geometry_for_tile is not None
                else tile.geometry
            )
            alpha = pygame.surfarray.array_alpha(geometry)
            red = pygame.surfarray.array_red(geometry)
            active_heights = red[alpha > 0]
            if active_heights.size:
                found_geometry = True
                collision_heights.append(int(active_heights.max()))

        if collision_heights:
            return max(collision_heights)
        if not found_geometry:
            return self.height + self.step_height + 1
        return None

    def _tile_height_at(self, grid_x, grid_y):
        height_at = getattr(self.tilemap, "tile_height_at", None)
        if height_at is not None:
            return height_at(grid_x, grid_y, self.height)

        heights = [
            self.tilemap.tileset.tile(layer[grid_y][grid_x]).height
            for layer in self.tilemap.layers
            if grid_y < len(layer) and grid_x < len(layer[grid_y])
        ]
        if not heights:
            return self.height
        return min(heights, key=lambda height: abs(self.height - height))


    def join(self, party, position=-1):
        party.add(self, position)

    def interact(self):
        dx = 0
        dy = 0
        if self.direction == 0: dy = 1
        elif self.direction == 1: dx = -1
        elif self.direction == 2: dx = 1
        elif self.direction == 3: dy = - 1

        target_x = self.grid_x + dx
        target_y = self.grid_y + dy
        if not (0 <= target_y < len(self.tilemap.tile_sprites)):
            return None
        if not (0 <= target_x < len(self.tilemap.tile_sprites[target_y])):
            return None

        tile_entity = self.tilemap.tile_sprites[target_y][target_x]
        if tile_entity:
            return tile_entity.on_interaction(tile_entity, self)

Entity = Sprite



class Party:
    '''Multiple sprites in a group following the leader.'''

    def __init__(self):
        self.leader = None
        self.sprites = []

    def __list__(self):
        return self.sprites
    
    def add(self, spite, position=-1):
        self.sprites.insert(position, spite)


class TileSprite:
    '''A sprite that is a tile, can be interacted with, or run code when loaded. These are created in the tilemap. Non-movable.'''
    def __init__(self, spritesheet, name):
        self.name = name
        self.direction = 0
        self.frame = 0
        self.spritesheet = spritesheet
        self.surface = self.spritesheet.surface(self.direction, self.frame)
        self.rect = self.surface.get_rect()
        self.grid_x = None
        self.grid_y = None
        self.x = None
        self.y = None

        self.on_entity_collision = None
        self.on_tile_collision = None
        self.on_interaction = None

    def interact(self, entity):
        if self.on_interaction:
            self.on_interaction(self, entity)
    
    def collide(self, entity):
        if self.on_entity_collision:
            self.on_entity_collision(self, entity)
