from pathlib import Path

texture = Path(__file__).with_name("gui.png").read_bytes()

tile_size = 16
mini_tile_size = 8