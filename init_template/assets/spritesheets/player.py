from pathlib import Path

texture = Path(__file__).with_name("player.png").read_bytes()
geometry = Path(__file__).with_name("player_g.png").read_bytes()
emision = Path(__file__).with_name("player_e.png").read_bytes()
filter = Path(__file__).with_name("player_f.png").read_bytes()