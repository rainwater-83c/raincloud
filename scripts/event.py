'''User-friendly events that are called by sprites or other things in the code.'''
from scripts import sprite

def move(entity: sprite.Sprite, direction: int | str, amount: int, speed: float = None):
    '''Moves an entity in a direction'''
    if not speed:
        speed = entity.speed
    if direction == 0 or direction == 'down':
        dx = 0
        dy = 1
    
    if direction == 1 or direction == 'left':
        dx = -1
        dy = 0

    if direction == 2 or direction == 'right':
        dx = 1
        dy = 0

    if direction == 3 or direction == 'up':
        dx = 0
        dy = -1
    
    for x in range(amount):
        entity.move(dx, dy, speed)

        while entity.moving:
            yield

def wait(seconds):
    timer = 0

    while timer < seconds:
        dt = yield
        timer += dt
    

