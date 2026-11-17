from collections.abc import Sequence
from io import BytesIO
from pathlib import Path

import pygame


texture = Path(__file__).with_name("font.png").read_bytes()
box_size = 8
SOURCE_WHITE = (255, 255, 255, 255)
SOURCE_BLACK = (0, 0, 0, 0)
_source = None
_atlas = None

SYMBOLS = (
	" ",
	"A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
	"M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
	"Y", "Z", ".", ":", "?", "-", "/",
    " ",
	"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
	"m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x",
	"y", "z", ",", ";", "!", "~", "\\",
)

SYMBOL_TO_INDEX = {symbol: index for index, symbol in enumerate(SYMBOLS)}


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


def set_palette(white, black=(0, 0, 0, 0)) -> None:
	"""Replace the sheet's white and black pixels, in that order."""
	global _atlas
	white = _rgba(white)
	black = _rgba(black)
	_atlas = _load_source().copy()
	for y in range(_atlas.get_height()):
		for x in range(_atlas.get_width()):
			color = tuple(_source.get_at((x, y)))
			if color == SOURCE_WHITE:
				_atlas.set_at((x, y), white)
			elif color == SOURCE_BLACK:
				_atlas.set_at((x, y), black)


def get_glyph(index: int) -> pygame.Surface:
	"""Return a row-major font cell cropped to its visible pixels."""
	atlas = _get_atlas()
	columns = atlas.get_width() // box_size
	rows = atlas.get_height() // box_size
	if not 0 <= index < columns * rows:
		raise IndexError(f"Font glyph index {index} is outside the font atlas")

	row, column = divmod(index, columns)
	cell = pygame.Rect(column * box_size, row * box_size, box_size, box_size)
	glyph = atlas.subsurface(cell)
	bounds = glyph.get_bounding_rect(min_alpha=1)
	if bounds.width == 0 or bounds.height == 0:
		return pygame.Surface((1, 1), pygame.SRCALPHA, 32)
	return glyph.subsurface(bounds).copy()


def get_symbol(symbol: str) -> pygame.Surface:
	"""Return the cropped glyph surface for one character."""
	try:
		index = SYMBOL_TO_INDEX[symbol]
	except KeyError as error:
		raise KeyError(f"Unsupported font character: {symbol!r}") from error
	return get_glyph(index)