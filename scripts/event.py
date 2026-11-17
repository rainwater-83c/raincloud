'''User-friendly events that are called by sprites or other things in the code.'''
from . import sprite
from .userinterface import DialogueBox
from .userinterface import DialogueBox
#from scripts.eventvars import ds


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


def dialogue(entity, location, text, font="font", colors=None):
    """Display dialogue until confirm is pressed."""
    app = getattr(entity, "app", None)
    if app is None:
        app = getattr(getattr(entity, "tilemap", None), "app", None)
    if app is None:
        raise ValueError("Dialogue entity is not attached to an App")

    app.dialogue_box = DialogueBox(app, entity, location, text, font, colors)
    ignore_current_confirm = "confirm" in app.just_pressed
    try:
        while True:
            yield
            if "confirm" not in app.just_pressed:
                ignore_current_confirm = False
            elif ignore_current_confirm:
                ignore_current_confirm = False
            else:
                app.just_pressed.remove("confirm")
                return
    finally:
        app.dialogue_box = None


def dialogue(
    entity,
    location: str,
    text: str,
    font="font",
    colors=None,
):
    """Show a dialogue box until the player confirms it."""
    app = getattr(entity, "app", None)
    if app is None:
        app = getattr(getattr(entity, "tilemap", None), "app", None)
    if app is None:
        raise ValueError("Dialogue entity is not attached to an App")

    app.dialogue_box = DialogueBox(app, entity, location, text, font, colors)
    try:
        while "confirm" in app.just_pressed:
            yield
        while True:
            yield
            if "confirm" in app.just_pressed:
                app.just_pressed.remove("confirm")
                break
    finally:
        app.dialogue_box = None

# Sets PS5 LED color
def set_PS5_led(color):
    ...#ds.light.setColorI(color[0], color[1], color[2])
    yield

# Sets PS5 haptic triggers
def set_PS5_trigger(trigger, mode, threshold):
    if trigger == 'l' or trigger == 'left':
        ...#ds.triggerL.setMode(mode)
        ...#ds.triggerL.setForce(1, threshold)

    if trigger == 'r' or trigger == 'right':
        ...#ds.triggerR.setMode(mode)
        ...#ds.triggerR.setForce(1, threshold)
    yield
    


    

