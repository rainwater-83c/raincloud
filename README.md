# Raincloud Game Engine

Raincloud is a Python game engine and command-line toolkit for building 2D games
with Pygame.

## Install

```bash
python -m pip install raincloud-engine
```

## Create a project

```bash
raincloud init ./my-game
```

This creates a starter game project with its sample assets. Run the game with
Python:

```bash
python ./my-game/main.py
```

## GPU lighting

Install the optional GPU dependency:

```bash
python -m pip install "raincloud-engine[gpu]"
```

Set `GPU_LIGHTING = True` in the game's `config.py` to enable the ModernGL
compositor and direct OpenGL presentation, which avoids reading the lit frame
back to the CPU. Scene drawing and sun-shadow projection still use the Pygame
canvas. If OpenGL initialization fails, the engine falls back to software
display and lighting.

## Build a distribution

Install the optional Nuitka build dependency, then build the project:

```bash
python -m pip install "raincloud-engine[build]"
raincloud build ./my-game
```

The distribution is written to `my-game/dist` by default. Building a native
executable may also require platform-specific system tools, such as a C compiler.