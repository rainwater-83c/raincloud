import argparse
import pathlib
import pygame

__version__ = "0.0.0 PT"

FORMAT = 0

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", type=pathlib.Path)
parser.add_argument("-s", "--tile-size", type=int)
args = parser.parse_args()

print(f"tileset converter version {__version__}")

path = pathlib.Path(args.path)

with open(path, "rb") as f:
    content = f.read()

img = pygame.image.load(path)
width, height = img.get_size()

gridwidth = int(width / args.tile_size)
gridheight = int(height / args.tile_size)

tiles = []
for h in range(gridheight):
    for w in range(gridwidth):
        tiles.append((w * args.tile_size, h * args.tile_size))


with open(f"{path.stem}.py", "w") as f:
    f.write(f"""
format = {FORMAT}
name = "{path.stem}"
tile_size = {args.tile_size}
content = {content}
priority = {(0,)*len(tiles)}
""")