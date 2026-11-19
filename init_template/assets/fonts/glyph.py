"""Read and recolor tightly cropped glyphs from the font atlas."""

from collections.abc import Sequence
from io import BytesIO
from pathlib import Path

import pygame


texture = Path(__file__).with_name("glyphs.png").read_bytes()
box_size = 8
GLYPH_COMPONENTS = (
	"", "A", "AI", "B", "D", "DH", "DY", "E", "F", "G",
	"H", "I", "K", "L", "M", "N", "O", "P", "R", "S",
	"SY", "T", "TH", "TY", "U", "V", "W", "Y", "Z", "ZY",
)
GLYPH_COMPONENT_TO_INDEX = {
	component: index for index, component in enumerate(GLYPH_COMPONENTS)
}
GLYPH_PAIR_TO_INDEX = {
	(left, right): left_index * len(GLYPH_COMPONENTS) + right_index
	for left_index, left in enumerate(GLYPH_COMPONENTS)
	for right_index, right in enumerate(GLYPH_COMPONENTS)
}
SOURCE_COLORS = (
	(0, 0, 0, 255),
	(255, 255, 255, 255),
	(128, 128, 128, 255),
)
_source = None
_atlas = None


def _rgba(color: Sequence[int]) -> pygame.Color:
	if len(color) == 3:
		return pygame.Color(*color, 255)
	if len(color) == 4:
		return pygame.Color(*color)
	raise ValueError("Font colors must be RGB or RGBA sequences")


def _load_source() -> pygame.Surface:
	global _source
	if _source is None:
		_source = pygame.image.load(BytesIO(texture))
	return _source


def _get_atlas() -> pygame.Surface:
	global _atlas
	if _atlas is None:
		_atlas = _load_source().copy()
	return _atlas


def set_palette(black, white, gray) -> None:
	"""Replace the atlas's opaque black, white, and gray pixels."""
	global _atlas
	replacements = tuple(_rgba(color) for color in (black, white, gray))
	_atlas = _load_source().copy()
	for y in range(_atlas.get_height()):
		for x in range(_atlas.get_width()):
			color = tuple(_source.get_at((x, y)))
			for original, replacement in zip(SOURCE_COLORS, replacements):
				if color == original:
					_atlas.set_at((x, y), replacement)
					break


def get_glyph(index: int) -> pygame.Surface:
	"""Return one row-major atlas cell cropped to its visible pixels."""
	atlas = _get_atlas()
	columns = atlas.get_width() // box_size
	rows = atlas.get_height() // box_size
	if not 0 <= index < columns * rows:
		raise IndexError(f"Glyph index {index} is outside the font atlas")

	row, column = divmod(index, columns)
	cell = pygame.Rect(column * box_size, row * box_size, box_size, box_size)
	glyph = atlas.subsurface(cell)
	bounds = glyph.get_bounding_rect(min_alpha=1)
	if bounds.width == 0 or bounds.height == 0:
		return pygame.Surface((1, 1), pygame.SRCALPHA, 32)
	return glyph.subsurface(bounds).copy()


def get_glyph_pair(left: str, right: str) -> pygame.Surface:
	"""Return the glyph formed by the indexed left and right components."""
	try:
		index = GLYPH_PAIR_TO_INDEX[(left.strip().upper(), right.strip().upper())]
	except KeyError as error:
		raise KeyError(f"Unknown glyph pair: <{left}|{right}>") from error
	return get_glyph(index)


def resolve_inline(value: str) -> pygame.Surface:
	"""Resolve inline glyph syntax such as ``A|A`` or ``glyph;A|A``."""
	value = value.strip()
	if value.startswith("glyph;"):
		value = value[len("glyph;"):].strip()
	if "|" not in value:
		raise KeyError(f"Inline glyph requires left and right components: {value!r}")
	left, right = value.split("|", 1)
	return get_glyph_pair(left, right)