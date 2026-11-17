from pygame.locals import (
    JOYAXISMOTION,
    JOYBUTTONDOWN,
    JOYBUTTONUP,
    KEYDOWN,
    KEYUP,
    QUIT,
)


def _set_action(app, action, pressed):
    if pressed and action not in app.pressed_keys:
        app.pressed_keys.append(action)
    elif not pressed and action in app.pressed_keys:
        app.pressed_keys.remove(action)


def quit_game(app, event):
    app.running = False


def key_down(app, event):
    for action, bindings in app.keybinds.items():
        if event.key in bindings:
            app.just_pressed.append(action)
            _set_action(app, action, True)


def key_up(app, event):
    for action, bindings in app.keybinds.items():
        if event.key in bindings:
            _set_action(app, action, False)


def joy_button_down(app, event):
    for action, bindings in app.gamepad_keybinds.items():
        if event.button in bindings:
            app.just_pressed.append(action)
            _set_action(app, action, True)


def joy_button_up(app, event):
    for action, bindings in app.gamepad_keybinds.items():
        if event.button in bindings:
            _set_action(app, action, False)


def joy_axis_motion(app, event):
    deadzone = 0.4
    if event.axis == 0:
        _set_action(app, "right", event.value > deadzone)
        _set_action(app, "left", event.value < -deadzone)
    elif event.axis == 1:
        _set_action(app, "down", event.value > deadzone)
        _set_action(app, "up", event.value < -deadzone)


def move_down(app):
    app.player.move(0, 1)


def move_up(app):
    app.player.move(0, -1)


def move_left(app):
    app.player.move(-1, 0)


def move_right(app):
    app.player.move(1, 0)


def confirm(app):
    if not app.script:
        app.script = app.player.interact()


def deny(app):
    if app.menu is None:
        app.open_menu("pause")
    else:
        app.close_menu()


EVENTS = {
    QUIT: quit_game,
    KEYDOWN: key_down,
    KEYUP: key_up,
    JOYBUTTONDOWN: joy_button_down,
    JOYBUTTONUP: joy_button_up,
    JOYAXISMOTION: joy_axis_motion,
}

KEYS = {
    "down": move_down,
    "up": move_up,
    "left": move_left,
    "right": move_right,
}

ONCE_KEYS = {
    "confirm": confirm,
    "deny": deny,
}