'''The main script. This is where the code for the event loop goes.'''

import pygame
from pygame.locals import *
import logging
from scripts.tilemap import Tilemap
from scripts import sprite
import coloredlogs
from inputs import get_gamepad
from assets.sprites import sprites


__version__ = "0.0.0 PT"

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG' if True else 'LOG', logger=logger,fmt="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.basicConfig(filename="logs/latest.log")
logger.debug(f"app script loaded! version: {__version__}")

# constant vars; not meant to be changed

DEFAULT_KEYBINDS = {
    "up": [K_w, K_UP],
    "down": [K_s, K_DOWN],
    "left": [K_a, K_LEFT],
    "right": [K_d, K_RIGHT],
    "confirm": [K_z, K_RETURN, K_SPACE, 'm0'],
    "deny": [K_x, K_ESCAPE, 'm1'],
    "run": [K_LSHIFT, K_RSHIFT]
}   

DEFAULT_GAMEPAD_KEYBINDS = {
    "up": [11],
    "down": [12],
    "left": [13],
    "right": [14],
    "confirm": [0],
    "deny": [1],
    "run": [K_LSHIFT, K_RSHIFT]
}   


class Camera:
    '''The main camera object.'''
    def __init__(self, width:int, height: int):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0

    def apply(self, rect: pygame.Rect):
        return rect.move(-self.offset_x, -self.offset_y)

    def update(self, target: sprite.Sprite, screen_w: int, screen_h: int):
        self.offset_x = target.x - screen_w // 2
        self.offset_y = target.y - screen_h // 2

        self.offset_x = max(0, min(self.offset_x, self.width - screen_w))
        self.offset_y = max(0, min(self.offset_y, self.height - screen_h))
        return self


class App:
    '''The main app.''' # help string
    def __init__(self, tilemap: Tilemap):
        pygame.init()
        #icon_image = pygame.image.load('my_icon.png')
        #pygame.display.set_icon(icon_image)
        pygame.display.set_caption("Raincloud game engine")
        flags = RESIZABLE
        self.screen = pygame.display.set_mode((800, 600))
        self.running = False
        self.keybinds = DEFAULT_KEYBINDS
        self.gamepad_keybinds = DEFAULT_GAMEPAD_KEYBINDS
        self.pressed_keys = []  # blank list for held keys
        self.tilemap = tilemap
        self.camera = Camera(self.tilemap.width, self.tilemap.height)
        self.party = sprite.Party()
        self.player = sprites['player'](self.tilemap)
        self.party.leader = self.player
        self.sprites = [self.player]
        self.clock = pygame.time.Clock()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.rumble(240, 500, 5)
        self.script = None
        self.just_pressed = []
    
    # function is defined with _ at the start to show that this function isnt meant to be used out of this class
    def _keydown(self, event):
        for key, value in self.keybinds.items():
            if event.key in value:
                self.just_pressed.append(key)
                self.pressed_keys.append(key)
                logger.debug(key)

    def _keyup(self, event):
        for key, value in self.keybinds.items():
            if event.key in value:
                self.pressed_keys.remove(key)
                logger.debug(key)

    def _joybuttondown(self, event):
        for key, value in self.gamepad_keybinds.items():
            if event.button in value:
                self.just_pressed.append(key)
                self.pressed_keys.append(key)
                logger.debug(key)

    def _joybuttonup(self, event):
        for key, value in self.gamepad_keybinds.items():
            if event.button in value:
                self.pressed_keys.remove(key)
                logger.debug(key)

    def _joyaxismotion(self, event):
        DEADZONE = 0.4
        
        if event.axis == 0:
            if event.value > DEADZONE:
                if 'right' not in self.pressed_keys: self.pressed_keys.append('right')
                if 'left' in self.pressed_keys: self.pressed_keys.remove('left')
            elif event.value < -DEADZONE:
                if 'left' not in self.pressed_keys: self.pressed_keys.append('left')
                if 'right' in self.pressed_keys: self.pressed_keys.remove('right')
            else:
                if 'left' in self.pressed_keys: self.pressed_keys.remove('left')
                if 'right' in self.pressed_keys: self.pressed_keys.remove('right')


        elif event.axis == 1:
            if event.value > DEADZONE:
                if 'down' not in self.pressed_keys: self.pressed_keys.append('down')
                if 'up' in self.pressed_keys: self.pressed_keys.remove('up')
            elif event.value < -DEADZONE:
                if 'up' not in self.pressed_keys: self.pressed_keys.append('up')
            else:
                if 'up' in self.pressed_keys: self.pressed_keys.remove('up')
                if 'down' in self.pressed_keys: self.pressed_keys.remove('down')

    def run(self):
        self.running = True
        while self.running:
            self.just_pressed.clear()
            dt = self.clock.tick(60) / 1000.0

            # ---------------- EVENTS ----------------

            for event in pygame.event.get():

                if event.type == QUIT:
                    self.running = False

                elif event.type == KEYDOWN:
                    self._keydown(event)

                elif event.type == KEYUP:
                    self._keyup(event)

                elif event.type == JOYBUTTONDOWN:
                    self._joybuttondown(event)

                elif event.type == JOYBUTTONUP:
                    self._joybuttonup(event)

                elif event.type == JOYAXISMOTION:
                    self._joyaxismotion(event)

            # ---------------- MOVEMENT ----------------

            if 'down' in self.pressed_keys: 
                self.player.move(0,1) 
            elif 'up' in self.pressed_keys: 
                self.player.move(0,-1) 
            elif 'left' in self.pressed_keys: 
                self.player.move(-1,0) 
            elif 'right' in self.pressed_keys: 
                self.player.move(1,0)
            else:
                self.player.move(0,0)
            
            if 'confirm' in self.just_pressed and not self.script:
                self.script = self.player.interact()

            # ---------------- UPDATE ----------------

            self.player.update(dt, self.player.speed*2 if not 'run' in self.pressed_keys else self.player.speed)

            # IMPORTANT:
            # rect MUST follow world position
            self.player.rect.midbottom = (self.player.x, self.player.y)

            self.camera.update(
                self.player,
                self.screen.get_width(),
                self.screen.get_height()
            )

            if self.script:
                try:
                    next(self.script)
                except StopIteration:
                    self.script = None

            # ---------------- RENDER ----------------

            self.screen.fill((0, 0, 0))

            # Ground layer
            self.screen.blit(
                self.tilemap.ground_tiles,
                (-self.camera.offset_x, -self.camera.offset_y)
            )

            # Depth-sorted sprites
            render_list = []

            for spr in self.sprites:
                depth = spr.rect.bottom
                render_list.append((depth, spr))

            for y, yc in enumerate(self.tilemap.tile_sprites):
                for x, spr in enumerate(yc):
                    if spr:
                        depth = spr.rect.bottom
                        render_list.append((depth, spr))

            render_list.sort(key=lambda x: x[0])

            for depth, spr in render_list:
                self.screen.blit(
                    spr.surface,
                    self.camera.apply(spr.rect)
                )

            # Priority layer
            self.screen.blit(
                self.tilemap.priority_tiles,
                (-self.camera.offset_x, -self.camera.offset_y)
            )

            pygame.display.flip()

        pygame.quit()
