import pytmx
import argparse
import pathlib
import pygame
import pprint

pygame.init()
pygame.display.set_mode((1, 1))

FORMAT = 0

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", type=pathlib.Path)
parser.add_argument("-n", "--name", type=str)
parser.add_argument("-t", "--tileset", type=str)
args = parser.parse_args()

tmx_data = pytmx.load_pygame(args.path)


w = tmx_data.width
h = tmx_data.height
l = len(tmx_data.layers)
layers = tmx_data.layers

size = (w, h, l)
tilemap = [[[0 for _ in range(int(size[0]))] for _ in range(int(size[1]))] for _ in range(int(size[2]))]

layers.reverse()

tiled_gids = [z for z in tmx_data.gidmap]

for index, layer in enumerate(layers):
    print(layer.name)
    for x, y, gid in layer:
        if gid > 0:
            id = tiled_gids[int(gid - 1)] -1
        else:
            id = 0
        tilemap[index][y][x] = id
    
print([z for z in tmx_data.gidmap])

tileset = args.tileset
name = args.name

with open(f"{name}.py", "w") as f:
    f.write(f"""
format = {FORMAT}
name = "{name}"
tile_sprites = "{[]}"
content = {tilemap}
tileset = "{tileset}"
""")