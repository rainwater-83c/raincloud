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

## Dialogue

Use the yielding `dialogue` event inside an interaction callback:

```python
from raincloud.scripts.event import dialogue

def talk_to_npc(self, player):
	yield from dialogue(
		self,
		"bottom",
		"test.. < |A><A|AI>",
		"font",
		colors={"text": (245, 248, 250), "panel": None},
	)
```

Dialogue stays open until the configured confirm action is pressed. Locations
are `"top"`, `"middle"`, or `"bottom"`. Glyph tags use
`<left_component|right_component>` and follow the 30-by-30 ordering in
`assets/fonts/glyph.py`: `< |A>` is index 1, `<A| >` is index 30, and `<A|AI>`
is index 32. Component names are case-insensitive, so `"<a|b>"` selects the
`A|B` glyph. A tag whose left side is a registered font alias instead renders
its right side as text, for example `<other|hello>`.

`colors` may be a GUI palette tuple, a text RGB/RGBA tuple, or a mapping with
`"panel"` and `"text"` entries.

## GPU lighting

Install the optional GPU dependency:

```bash
python -m pip install "raincloud-engine[gpu]"
```

Set `GPU_LIGHTING = True` in the game's `config.py` to enable the ModernGL
compositor and direct OpenGL presentation, which avoids reading the lit frame
back to the CPU. Static sun shadows are projected on the GPU each simulation
tick; scene drawing and dynamic sprite shadows still use Pygame. If OpenGL
initialization fails, the engine falls back to software display and lighting.

## Build a distribution

Install the optional Nuitka build dependency, then build the project:

```bash
python -m pip install "raincloud-engine[build]"
raincloud build ./my-game
```

The distribution is written to `my-game/dist` by default. Building a native
executable may also require platform-specific system tools, such as a C compiler.