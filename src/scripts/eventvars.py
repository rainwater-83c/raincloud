from pydualsense import pydualsense, TriggerModes

ds = pydualsense()
try:
    ds.init()
except Exception as e:
    pass
else:
    PS5_BATTERY_LEVEL = ds.battery.Level
    PS5_BATTERY_STATE = ds.battery.State

RED = (255, 0, 0)
ORANGE = (255, 128, 0)
YELLOW = (255, 255, 0)
LIME = (128, 255, 0)
GREEN = (0, 255, 0)
AQUA = (0, 255, 128)
CYAN = (0, 255, 255)
LIGHT_BLUE = (0, 128, 255)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 255)
MAGENTA = (255, 0, 255)
HOT_PINK = (255, 0, 128)

BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

BROWN = (128, 64, 0)

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


