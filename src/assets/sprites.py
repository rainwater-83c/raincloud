from scripts.sprite import Sprite, TileSprite, Spritesheet
from scripts.event import *
from scripts.eventvars import *

sprites = {}

sprites['player'] = lambda tilemap: Sprite(Spritesheet('niko', 4), 'Player', 5, 5, tilemap)
sprites['safe'] = TileSprite(Spritesheet('blue_safe', 4), 'safe')

def safe_on_interaction(self, target):
    yield from set_PS5_led(RED)
    yield from wait(30)
    yield from set_PS5_led(YELLOW)
    yield from wait(30)
    yield from set_PS5_led(GREEN)
    yield from wait(30)
    yield from set_PS5_led(CYAN)
    yield from wait(30)
    yield from set_PS5_led(BLUE)
    yield from wait(30)
    yield from set_PS5_led(MAGENTA)
    yield from wait(30)
    yield from set_PS5_led(BLACK)

sprites['safe'].on_interaction = safe_on_interaction

