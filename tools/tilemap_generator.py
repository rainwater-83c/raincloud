import argparse
from pprint import pprint
from pathlib import Path

__version__ = "0.0.0 PT"

FORMAT = 0

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", type=str)
parser.add_argument("-s", "--size", type=str)
parser.add_argument("-t", "--tileset", type=str)
args = parser.parse_args()


tileset = args.tileset
size = args.size.split(",")
name = args.name
print(size)

print(f"tilemap generator version {__version__}")

zero = [0]

tilemap = [[[0 for _ in range(int(size[0]))] for _ in range(int(size[1]))] for _ in range(int(size[2]))]

with open(f"{name}.py", "w") as f:
    f.write(f"""
format = {FORMAT}
name = "{name}"
content = {tilemap}
tileset = "{tileset}"
""")


