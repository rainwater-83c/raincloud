'''User-friendly events that are called by sprites or other things in the code.'''
from scripts import sprite
from scripts.eventvars import ds


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

# Waits for a set amount of frames
def wait(frames):
    for _ in range(frames):
        yield

# Sets PS5 LED color
def set_PS5_led(color):
    ds.light.setColorI(color[0], color[1], color[2])
    yield

# Sets PS5 haptic triggers
def set_PS5_trigger(trigger, mode, threshold):
    if trigger == 'l' or trigger == 'left':
        ds.triggerL.setMode(mode)
        ds.triggerL.setForce(1, threshold)

    if trigger == 'r' or trigger == 'right':
        ds.triggerR.setMode(mode)
        ds.triggerR.setForce(1, threshold)
    yield
    


    

