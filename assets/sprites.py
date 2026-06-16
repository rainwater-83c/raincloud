from scripts.sprite import Sprite, TileSprite, Spritesheet
from scripts.event import *
from scripts.keywordvars import *

sprites = {}

sprites['player'] = lambda tilemap: Sprite(Spritesheet('niko', 4), 'Player', 5, 5, tilemap)
sprites['safe'] = TileSprite(Spritesheet('blue_safe', 4), 'safe')

def safe_on_interaction(self, target):
    yield from move(target, LEFT, 1)
    yield from move(target, UP, 2)
    yield from move(target, RIGHT, 2)
    yield from move(target, DOWN, 2)
    yield from move(target, LEFT, 1)

sprites['safe'].on_interaction = safe_on_interaction

