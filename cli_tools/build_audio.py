import argparse
import pathlib
import pygame

__version__ = "0.0.0 PT"

FORMAT = 0

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", type=pathlib.Path)
args = parser.parse_args()

print(f"audio converter version {__version__}")

path = pathlib.Path(args.path)

with open(path, "rb") as f:
    audio_data = f.read()

with open(f"{path.stem}.py", "w") as f:
    f.write(f"""
format = {FORMAT}
name = "{path.stem}"
audio = {audio_data}
""")