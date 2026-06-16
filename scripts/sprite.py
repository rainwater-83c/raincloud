'''
Load sprite files into objects.
Spritesheet extension is .rcs
'''

import pygame
import logging
import coloredlogs
from pathlib import Path
from scripts import reusable, tilemap
from functools import wraps


__version__ = "0.0.0 PT"

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"sprite script loaded! version: {__version__}")

FORMAT = 0
'''The sprite file format.'''

class Spritesheet:
    def __init__(self, name: str, frames: int):
        self.name = name
        self.frames = frames
        self.path = Path(f"assets/spritesheets/{name}.py").absolute()
        self.module = reusable.path_to_module(self.path, FORMAT)
        self.image = reusable.bytes_to_image(self.module.content)

    def surface(self, direction: int, frame: int):
        self.rect = pygame.rect.Rect(((frame/4)*self.image.get_width(), (direction/4)*self.image.get_height()), (self.image.get_width()/4, self.image.get_height()/4))
        return self.image.subsurface(self.rect)

class Sprite(pygame.sprite.Sprite):
    '''An event or object that moves or is interactable. Also known as an entity.'''

    def __init__(self, spritesheet: Spritesheet, name: str, x: int, y: int, tilemap, direction: int=0, speed: int=1.25):
        super().__init__()
        self.path = name
        self.spritesheet = spritesheet
        self.tilemap = tilemap
        self.grid_x = x
        self.grid_y = y
        self.target_x = None
        self.target_y = None
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
        self.rect = self.surface.get_rect()
        self.moving = False
        self.buffered_input = None
        self.anim_timer = 0
        self.move_speed = 0
        self.movenext = False
        self.nextprogress = 0
        self.walk_cycle = 0
        self.anim_timer = 0

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
        

    def move(self, dx:int, dy:int, speed=1):
        if self.moving:
            if dx == 1:
                tempdirection = 2
                self.movenext = True
            elif dx == -1:
                tempdirection = 1
                self.movenext = True
            elif dy == 1:
                tempdirection = 0
                self.movenext = True
            elif dy == -1:
                tempdirection = 3
                self.movenext = True
            elif dx == 0 and dy == 0:
                #tempdirection = -1
                self.movenext = False
                return
            if not tempdirection == self.direction:
                self.buffered_input = (dx, dy)
            return
        if dx == 1:
            self.direction = 2
            self.movenext = True
        elif dx == -1:
            self.direction = 1
            self.movenext = True
        elif dy == 1:
            self.direction = 0
            self.movenext = True
        elif dy == -1:
            self.direction = 3
            self.movenext = True
        elif dx == 0 and dy == 0:
            self.movenext = False
            return
        if False:
            pass
        else:
            if not self.tilemap.collision[self.grid_y+dy][self.grid_x+dx]:
                self.move_timer = 0

                self.start_x = self.x
                self.start_y = self.y

                self.grid_x += dx
                self.grid_y += dy

                tile_size = self.tilemap.tileset.tile_size

                self.target_x = (self.grid_x) * tile_size + tile_size // 2
                self.target_y = ((self.grid_y) + 1) * tile_size
            
                self.move_speed = speed
            
                self.moving = True
            


    def join(self, party, position=-1):
        party.add(self, position)

    def interact(self):
        dx = 0
        dy = 0
        if self.direction == 0: dy = 1
        elif self.direction == 1: dx = -1
        elif self.direction == 2: dx = 1
        elif self.direction == 3: dy = - 1

        tile_entity = self.tilemap.tile_sprites[self.grid_y + dy][self.grid_x + dx]
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
