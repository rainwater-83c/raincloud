from pygame.locals import (
    K_a,
    K_d,
    K_DOWN,
    K_ESCAPE,
    K_LSHIFT,
    K_RETURN,
    K_RIGHT,
    K_s,
    K_SPACE,
    K_UP,
    K_w,
    K_x,
    K_z,
    K_LEFT,
)


KEYBINDS = {
    "up": [K_w, K_UP],
    "down": [K_s, K_DOWN],
    "left": [K_a, K_LEFT],
    "right": [K_d, K_RIGHT],
    "confirm": [K_z, K_RETURN, K_SPACE, "m0"],
    "deny": [K_x, K_ESCAPE, "m1"],
    "run": [K_LSHIFT],
}

GAMEPAD_KEYBINDS = {
    "up": [11],
    "down": [12],
    "left": [13],
    "right": [14],
    "confirm": [0],
    "deny": [1],
    "run": [],
}