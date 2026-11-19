'''UI texture generation and menu controller.'''

import io
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

import pygame

try:
    from assets.gui.gui import (
        mini_tile_size as GUI_MINI_TILE_SIZE,
        texture as DEFAULT_GUI_TEXTURE,
        tile_size as GUI_TILE_SIZE,
    )
except ModuleNotFoundError:
    from src.assets.gui.gui import (
        mini_tile_size as GUI_MINI_TILE_SIZE,
        texture as DEFAULT_GUI_TEXTURE,
        tile_size as GUI_TILE_SIZE,
    )


SHADE_VALUES = (16, 32, 64, 128, 160, 176, 184, 192)
TILE_SIZE = GUI_TILE_SIZE
Matrix = tuple[tuple[int, ...], ...]
Palette = tuple[tuple[int, int, int, int] | None, ...]


@dataclass(frozen=True)
class Button:
    label: str
    action: Callable | None = None
    menu: str | None = None
    matrix: Matrix | None = None
    colors: Palette | None = None
    selected_colors: Palette | None = None
    corner_type: str | None = None
    edge_style: str | None = None


@dataclass(frozen=True)
class Slider:
    """A horizontal slider control with a label, value range, and change callback."""

    label: str
    min_value: float = 0.0
    max_value: float = 1.0
    step: float = 0.1
    default: float = 0.5
    action: Callable | None = None
    matrix: Matrix | None = None
    colors: Palette | None = None


@dataclass(frozen=True)
class Menu:
    title: str
    matrix: Matrix
    buttons: tuple[Button, ...]
    colors: Palette
    sliders: tuple[Slider, ...] = ()
    corner_type: str = "rounded"
    edge_style: str = "straight"
    button_matrix: Matrix = (
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    )
    button_colors: Palette = (
        (26, 34, 45, 235),
        (34, 46, 60, 235),
        (48, 64, 80, 235),
        (66, 84, 101, 235),
        (89, 110, 127, 235),
        (122, 144, 159, 235),
        (163, 183, 197, 235),
        (220, 232, 240, 235),
    )
    selected_button_colors: Palette = (
        (29, 48, 49, 245),
        (35, 67, 65, 245),
        (43, 91, 83, 245),
        (56, 120, 104, 245),
        (82, 153, 126, 245),
        (121, 186, 152, 245),
        (168, 216, 184, 245),
        (225, 245, 230, 245),
    )
    slider_colors: Palette = (
        (60, 75, 95, 235),
        (90, 110, 135, 235),
        (120, 145, 170, 235),
        (220, 232, 240, 235),
    )
    selected_slider_colors: Palette = (
        (70, 90, 110, 245),
        (100, 125, 150, 245),
        (140, 170, 200, 245),
        (225, 245, 230, 245),
    )


class GUITexture:
    def __init__(self, texture=DEFAULT_GUI_TEXTURE):
        if isinstance(texture, pygame.Surface):
            self.atlas = texture.copy()
        else:
            self.atlas = pygame.image.load(io.BytesIO(texture))
        if self.atlas.get_width() % GUI_TILE_SIZE or self.atlas.get_height() % GUI_TILE_SIZE:
            raise ValueError("GUI atlas dimensions must be multiples of the 16x16 tile size")
        if GUI_TILE_SIZE != GUI_MINI_TILE_SIZE * 2:
            raise ValueError("GUI tiles must be composed from 2x2 mini-tiles")

        self.mini_tile_columns = self.atlas.get_width() // GUI_MINI_TILE_SIZE
        self.mini_tile_rows = self.atlas.get_height() // GUI_MINI_TILE_SIZE
        self.mini_tiles = tuple(
            self.atlas.subsurface((
                column * GUI_MINI_TILE_SIZE,
                row * GUI_MINI_TILE_SIZE,
                GUI_MINI_TILE_SIZE,
                GUI_MINI_TILE_SIZE,
            )).copy()
            for row in range(self.mini_tile_rows)
            for column in range(self.mini_tile_columns)
        )
        self._palette_cache = {}

    def render(
        self,
        matrix: Sequence[Sequence[int]],
        colors: Sequence[tuple[int, ...] | None],
        corner_type: str = "rounded",
        edge_style: str = "straight",
    ) -> pygame.Surface:
        if not matrix or not matrix[0]:
            raise ValueError("GUI matrix must not be empty")
        if len(colors) != len(SHADE_VALUES):
            raise ValueError(f"Expected {len(SHADE_VALUES)} shade colors")
        matrix_width = len(matrix[0])
        if any(len(row) != matrix_width for row in matrix):
            raise ValueError("GUI matrix rows must all have the same width")
        if any(cell not in (0, 1) for row in matrix for cell in row):
            raise ValueError("GUI matrix cells must be 0 (empty) or 1 (filled)")
        if corner_type not in ("square", "rounded", "circle"):
            raise ValueError("corner_type must be square, rounded, or circle")
        if edge_style not in ("straight", "wiggly"):
            raise ValueError("edge_style must be straight or wiggly")

        mini_tiles = self._colored_mini_tiles(colors)
        corner_ids = {
            "square": {"top_left": 12, "top_right": 13, "bottom_left": 18, "bottom_right": 19},
            "rounded": {"top_left": 14, "top_right": 15, "bottom_left": 20, "bottom_right": 21},
            "circle": {"top_left": 16, "top_right": 17, "bottom_left": 22, "bottom_right": 23},
        }[corner_type]
        edge_ids = (
            {"top": 1, "bottom": 2, "left": 3, "right": 4}
            if edge_style == "straight"
            else {"top": 7, "bottom": 8, "left": 9, "right": 10}
        )
        result = pygame.Surface(
            (matrix_width * GUI_TILE_SIZE, len(matrix) * GUI_TILE_SIZE),
            pygame.SRCALPHA,
        )
        for tile_y, row in enumerate(matrix):
            for tile_x, occupied in enumerate(row):
                if not occupied:
                    continue

                top = tile_y == 0 or matrix[tile_y - 1][tile_x] == 0
                bottom = tile_y == len(matrix) - 1 or matrix[tile_y + 1][tile_x] == 0
                left = tile_x == 0 or row[tile_x - 1] == 0
                right = tile_x == matrix_width - 1 or row[tile_x + 1] == 0
                mini_ids = (
                    self._quadrant_tile(top, left, "top_left", edge_ids, corner_ids),
                    self._quadrant_tile(top, right, "top_right", edge_ids, corner_ids),
                    self._quadrant_tile(bottom, left, "bottom_left", edge_ids, corner_ids),
                    self._quadrant_tile(bottom, right, "bottom_right", edge_ids, corner_ids),
                )
                tile = self._compose_tile(mini_tiles, mini_ids)
                result.blit(
                    tile,
                    (tile_x * GUI_TILE_SIZE, tile_y * GUI_TILE_SIZE),
                )
        return result

    @staticmethod
    def _quadrant_tile(horizontal_edge, vertical_edge, corner_name, edge_ids, corner_ids):
        if horizontal_edge and vertical_edge:
            return corner_ids[corner_name]
        if horizontal_edge:
            return edge_ids["top" if corner_name.startswith("top") else "bottom"]
        if vertical_edge:
            return edge_ids["left" if corner_name.endswith("left") else "right"]
        return 5

    @staticmethod
    def _compose_tile(mini_tiles, mini_ids):
        tile = pygame.Surface((GUI_TILE_SIZE, GUI_TILE_SIZE), pygame.SRCALPHA)
        for index, mini_id in enumerate(mini_ids):
            mini_x = index % 2
            mini_y = index // 2
            tile.blit(
                mini_tiles[mini_id],
                (mini_x * GUI_MINI_TILE_SIZE, mini_y * GUI_MINI_TILE_SIZE),
            )
        return tile

    def _colored_mini_tiles(self, colors):
        palette = tuple(self._rgba(color) for color in colors)
        cached_tiles = self._palette_cache.get(palette)
        if cached_tiles is not None:
            return cached_tiles

        color_map = dict(zip(SHADE_VALUES, palette))
        colored_mini_tiles = []
        for mini_tile in self.mini_tiles:
            colored = pygame.Surface(mini_tile.get_size(), pygame.SRCALPHA)
            for y in range(GUI_MINI_TILE_SIZE):
                for x in range(GUI_MINI_TILE_SIZE):
                    red, green, blue, alpha = mini_tile.get_at((x, y))
                    if alpha == 0:
                        continue
                    if red != green or green != blue or red not in color_map:
                        raise ValueError(f"Unexpected gui.png shade: {(red, green, blue, alpha)}")
                    replacement = color_map[red]
                    if replacement[3]:
                        colored.set_at((x, y), replacement)
            colored_mini_tiles.append(colored)
        result = tuple(colored_mini_tiles)
        self._palette_cache[palette] = result
        return result

    @staticmethod
    def _rgba(color):
        if color is None:
            return (0, 0, 0, 0)
        if len(color) == 3:
            color = (*color, 255)
        if len(color) != 4 or any(channel < 0 or channel > 255 for channel in color):
            raise ValueError("Colors must be RGB/RGBA byte tuples or None")
        return tuple(color)

_default_gui = GUITexture()


DEFAULT_DIALOGUE_COLORS = (
    (22, 30, 42, 245),
    (28, 38, 52, 245),
    (38, 50, 66, 245),
    (54, 68, 84, 245),
    (75, 91, 108, 245),
    (109, 127, 144, 245),
    (160, 177, 191, 245),
    (232, 240, 245, 245),
)
DEFAULT_DIALOGUE_TEXT_COLOR = (245, 248, 250)
INLINE_FONT_PATTERN = re.compile(r"<([^<>]+)>")

class DialogueBox:
    def __init__(self, app, entity, location, text, font, colors=None):
        if location not in ("top", "bottom", "middle"):
            raise ValueError("Dialogue location must be top, bottom, or middle")

        self.app = app
        self.entity = entity
        self.location = location
        self.text_color = DEFAULT_DIALOGUE_TEXT_COLOR
        self.panel_colors = DEFAULT_DIALOGUE_COLORS
        if isinstance(colors, dict):
            self.text_color = colors.get("text") or self.text_color
            self.panel_colors = colors.get("panel") or self.panel_colors
        elif colors is not None:
            if len(colors) == len(SHADE_VALUES):
                self.panel_colors = colors
            else:
                self.text_color = colors

        self.fonts = dict(getattr(app, "dialogue_fonts", {}))
        if isinstance(font, dict):
            self.fonts.update(font)
            self.font = self._resolve_font(
                font.get("default", self.fonts.get("font"))
            )
        else:
            self.font = self._resolve_font(font)
        if self.font is None:
            raise ValueError("Dialogue needs a default font")

        self.lines = self._layout_text(text)
        content_width = max((sum(glyph.get_width() for glyph in line) for line in self.lines), default=1)
        line_height = max((glyph.get_height() for line in self.lines for glyph in line), default=1)
        padding_x = 12
        padding_y = 8
        columns = max(3, math.ceil((content_width + padding_x * 2) / GUI_TILE_SIZE))
        rows = max(3, math.ceil((line_height * max(1, len(self.lines)) + padding_y * 2) / GUI_TILE_SIZE))
        matrix = tuple(tuple(1 for _ in range(columns)) for _ in range(rows))
        self.panel = make_gui_texture(matrix, self.panel_colors, "rounded", "straight")
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.line_height = line_height

    def _resolve_font(self, font):
        if isinstance(font, str):
            try:
                return self.fonts[font]
            except KeyError as error:
                raise KeyError(f"Unknown dialogue font: {font}") from error
        return font

    def _render_character(self, font, character):
        if character == "\n":
            return pygame.Surface((1, 1), pygame.SRCALPHA, 32)
        if callable(getattr(font, "print", None)):
            return font.print(character, space_length=4)
        if isinstance(font, pygame.font.Font):
            return font.render(character, True, self.text_color)
        raise TypeError("Inline text fonts must provide print() or be a pygame font")

    def _render_glyph(self, font, symbol):
        if callable(getattr(font, "get_symbol", None)):
            return font.get_symbol(symbol)
        if not callable(getattr(font, "get_glyph", None)):
            return None

        symbol_map = getattr(font, "SYMBOL_TO_INDEX", {})
        if symbol in symbol_map:
            glyph_index = symbol_map[symbol]
        elif len(symbol) == 1:
            glyph_index = ord(symbol)
        else:
            try:
                glyph_index = int(symbol)
            except ValueError as error:
                raise ValueError(
                    f"Glyph {symbol!r} is not numeric and has no SYMBOL_TO_INDEX entry"
                ) from error
        return font.get_glyph(glyph_index)

    def _text_glyphs(self, font, text):
        if callable(getattr(font, "get_glyph", None)) or callable(getattr(font, "get_symbol", None)):
            if text == " ":
                return [self._render_character(self.font, text)]
            try:
                glyph_index = int(text)
            except ValueError:
                return [self._render_glyph(font, character) for character in text]
            return [font.get_glyph(glyph_index)]
        return [self._render_character(font, character) for character in text]

    def _layout_text(self, text):
        matches = list(INLINE_FONT_PATTERN.finditer(text))
        runs = []
        start = 0
        for match in matches:
            if match.start() > start:
                runs.append((self.font, text[start:match.start()], "text"))

            inline = match.group(1).strip()
            if ";" in inline:
                font_name, inline_text = inline.split(";", 1)
                run_font = self._resolve_font(font_name.strip())
                runs.append((run_font, inline_text.strip(), "inline"))
            elif "|" in inline:
                left, right = (part.strip() for part in inline.split("|", 1))
                if left in self.fonts:
                    runs.append((self._resolve_font(left), right, "font"))
                else:
                    raise KeyError(f"Unknown inline font: <{inline}>")
            else:
                raise KeyError(f"Unknown inline text tag: <{inline}>")
            start = match.end()
        if start < len(text) or not runs:
            runs.append((self.font, text[start:], "text"))

        max_width = max(1, self.app.screen.get_width() - 48)
        lines = [[]]
        line_widths = [0]
        for run_font, run_text, run_type in runs:
            if run_type == "inline":
                resolver = getattr(run_font, "resolve_inline", None)
                if not callable(resolver):
                    raise TypeError(f"Inline font {run_font.__class__.__name__} needs resolve_inline()")
                characters = ("",)
                glyphs = (resolver(run_text),)
            elif run_type == "font":
                characters = run_text
                glyphs = self._text_glyphs(run_font, run_text)
            else:
                characters = run_text
                glyphs = [self._render_character(run_font, char) for char in run_text]
            for character, glyph in zip(characters, glyphs):
                if character == "\n":
                    lines.append([])
                    line_widths.append(0)
                    continue
                if line_widths[-1] and line_widths[-1] + glyph.get_width() > max_width:
                    lines.append([])
                    line_widths.append(0)
                lines[-1].append(glyph)
                line_widths[-1] += glyph.get_width()
        return lines

    def render(self, screen):
        screen_rect = screen.get_rect()
        panel_rect = self.panel.get_rect(center=screen_rect.center)
        if self.location == "top":
            panel_rect.midtop = (screen_rect.centerx, 12)
        elif self.location == "bottom":
            panel_rect.midbottom = (screen_rect.centerx, screen_rect.bottom - 12)

        screen.blit(self.panel, panel_rect)
        y = panel_rect.top + self.padding_y
        for line in self.lines:
            line_width = sum(glyph.get_width() for glyph in line)
            x = panel_rect.left + (panel_rect.width - line_width) // 2
            for glyph in line:
                screen.blit(glyph, (x, y + self.line_height - glyph.get_height()))
                x += glyph.get_width()
            y += self.line_height


def make_gui_texture(
    matrix: Sequence[Sequence[int]],
    colors: Sequence[tuple[int, ...] | None],
    corner_type: str = "rounded",
    edge_style: str = "straight",
) -> pygame.Surface:
    return _default_gui.render(matrix, colors, corner_type, edge_style)


class MenuController:
    def __init__(self, name: str, app, definitions=None):
        if definitions is None:
            from assets.menus import MENUS
            definitions = MENUS

        if name not in definitions:
            raise KeyError(f"Unknown menu: {name}")

        self.name = name
        self.app = app
        self.definition = definitions[name]
        self.title = self.definition.title
        self.items = self.definition.buttons
        if not self.items:
            raise ValueError(f"Menu '{name}' must define at least one item")

        self.sliders = self.definition.sliders
        self.slider_values = [s.default for s in self.sliders]
        self.slider_rects = []
        self.active_slider = None  # index of slider currently being adjusted
        self.total_items = len(self.items) + len(self.sliders)
        if self.sliders:
            # Start on the first adjustable control in menus that contain sliders.
            self.selected = len(self.items)
        else:
            self.selected = 0

        self.gui = GUITexture()
        self.corner_type = self.definition.corner_type
        self.edge_style = self.definition.edge_style
        self.colors = self.definition.colors
        self.bitmap_font = app.bitmap_font
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        self.button_surfaces = []
        for button in self.items:
            matrix = button.matrix or self.definition.button_matrix
            corner_type = button.corner_type or self.corner_type
            edge_style = button.edge_style or self.edge_style
            colors = button.colors or self.definition.button_colors
            selected_colors = button.selected_colors or self.definition.selected_button_colors
            self.button_surfaces.append((
                self.gui.render(matrix, colors, corner_type, edge_style),
                self.gui.render(matrix, selected_colors, corner_type, edge_style),
            ))

        # Slider state
        self.sliders = self.definition.sliders
        self.slider_values = [s.default for s in self.sliders]
        self.slider_rects = []
        self.active_slider = None  # index of slider currently being adjusted
        self.total_items = len(self.items) + len(self.sliders)

        self.matrix = self.definition.matrix
        self.panel_surface = self.gui.render(
            self.matrix,
            self.colors,
            self.corner_type,
            self.edge_style,
        )
        self.panel_size = self.panel_surface.get_size()
        self.button_rects = []

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            for action, bindings in self.app.keybinds.items():
                if event.key not in bindings:
                    continue
                if action == "up":
                    if self.total_items > 0:
                        self.selected = (self.selected - 1) % self.total_items
                    return True
                elif action == "down":
                    if self.total_items > 0:
                        self.selected = (self.selected + 1) % self.total_items
                    return True
                elif action == "left" and self.sliders and self._is_slider_selected():
                    self._adjust_slider(self._slider_index(), -1)
                    return True
                elif action == "right" and self.sliders and self._is_slider_selected():
                    self._adjust_slider(self._slider_index(), 1)
                    return True
                elif action == "confirm":
                    if self._is_slider_selected():
                        pass
                    else:
                        self.activate()
                    return True
                elif action == "deny":
                    self.app.close_menu()
                    return True
                else:
                    continue

        elif event.type == pygame.KEYUP:
            for action, bindings in self.app.keybinds.items():
                if action in ("up", "down", "confirm", "deny") and event.key in bindings:
                    if action in self.app.pressed_keys:
                        self.app.pressed_keys.remove(action)
                    return True
            return False

        elif event.type == pygame.JOYBUTTONDOWN:
            for action, bindings in self.app.gamepad_keybinds.items():
                if event.button not in bindings:
                    continue
                if action == "up":
                    if self.total_items > 0:
                        self.selected = (self.selected - 1) % self.total_items
                elif action == "down":
                    if self.total_items > 0:
                        self.selected = (self.selected + 1) % self.total_items
                elif action == "left" and self.sliders and self._is_slider_selected():
                    self._adjust_slider(self._slider_index(), -1)
                elif action == "right" and self.sliders and self._is_slider_selected():
                    self._adjust_slider(self._slider_index(), 1)
                elif action == "confirm":
                    if not self._is_slider_selected():
                        self.activate()
                elif action == "deny":
                    self.app.close_menu()
                else:
                    continue
                return True

        elif event.type == pygame.JOYBUTTONUP:
            for action, bindings in self.app.gamepad_keybinds.items():
                if action in ("up", "down", "confirm", "deny") and event.button in bindings:
                    if action in self.app.pressed_keys:
                        self.app.pressed_keys.remove(action)
                    return True
            return False

        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    return True
            if self.active_slider is not None:
                self._set_slider_from_mouse(self.active_slider, event.pos)
                return True
            for index, rect in enumerate(self.slider_rects):
                if rect.collidepoint(event.pos):
                    self.selected = len(self.items) + index
                    return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    self.activate()
                    return True
            if self.slider_rects:
                for index, rect in enumerate(self.slider_rects):
                    if rect.collidepoint(event.pos):
                        self.selected = len(self.items) + index
                        self.active_slider = index
                        self._set_slider_from_mouse(index, event.pos)
                        return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.active_slider = None

        return False

    def _slider_value_to_position(self, index: int) -> float:
        """Convert a slider's current value to a 0-1 position along the track."""
        slider = self.sliders[index]
        value = self.slider_values[index]
        if slider.max_value <= slider.min_value:
            return 0.0
        return (value - slider.min_value) / (slider.max_value - slider.min_value)

    def _slider_position_to_value(self, index: int, position: float) -> float:
        """Convert a 0-1 track position to a slider value, snapped to step."""
        slider = self.sliders[index]
        position = max(0.0, min(1.0, position))
        raw_value = slider.min_value + position * (slider.max_value - slider.min_value)
        if slider.step > 0:
            raw_value = round(raw_value / slider.step) * slider.step
        return max(slider.min_value, min(slider.max_value, raw_value))

    def _adjust_slider(self, index: int, direction: int) -> None:
        """Adjust a slider value by one step in the given direction (-1 or 1)."""
        slider = self.sliders[index]
        new_value = self._slider_position_to_value(
            index,
            self._slider_value_to_position(index) + direction * slider.step,
        )
        self.slider_values[index] = new_value
        if slider.action is not None:
            slider.action(self.app, new_value)

    def _set_slider_from_mouse(self, index: int, mouse_pos: tuple[int, int]) -> None:
        """Set a slider's value based on a mouse position within its track."""
        slider = self.sliders[index]
        rect = self.slider_rects[index]
        track_x = rect.x + 8
        track_width = rect.width - 16
        if track_width <= 0:
            return
        position = (mouse_pos[0] - track_x) / track_width
        self.slider_values[index] = self._slider_position_to_value(index, position)
        if slider.action is not None:
            slider.action(self.app, self.slider_values[index])

    def _is_slider_selected(self) -> bool:
        """Return True if the current selection is on a slider."""
        return self.total_items > 0 and self.selected >= len(self.items)

    def _slider_index(self) -> int:
        """Return the index of the currently selected slider, or -1."""
        if self._is_slider_selected():
            return self.selected - len(self.items)
        return -1

    def _render_text(self, text: str, color: tuple[int, ...], size: int = 24) -> pygame.Surface:
        """Render text using the bitmap font if available, else pygame font."""
        matches = list(INLINE_FONT_PATTERN.finditer(text))
        if matches:
            surfaces = []
            cursor = 0
            for match in matches:
                if match.start() > cursor:
                    surfaces.append(self._render_text_plain(text[cursor:match.start()], color, size))
                inline = match.group(1).strip()
                if ";" not in inline:
                    raise KeyError(f"Inline text requires a font name: <{inline}>")
                font_name, inline_text = inline.split(";", 1)
                fonts = getattr(self.app, "dialogue_fonts", {})
                run_font = fonts.get(font_name.strip())
                resolver = getattr(run_font, "resolve_inline", None)
                if not callable(resolver):
                    raise KeyError(f"Unknown inline font or glyph resolver: {font_name.strip()!r}")
                glyph = resolver(inline_text.strip())
                if glyph.get_height() < size:
                    scale = size / glyph.get_height()
                    glyph = pygame.transform.scale(
                        glyph,
                        (max(1, int(glyph.get_width() * scale)), size),
                    )
                surfaces.append(glyph)
                cursor = match.end()
            if cursor < len(text):
                surfaces.append(self._render_text_plain(text[cursor:], color, size))
            height = max((surface.get_height() for surface in surfaces), default=size)
            width = sum(surface.get_width() for surface in surfaces)
            result = pygame.Surface((max(1, width), height), pygame.SRCALPHA, 32)
            x = 0
            for surface in surfaces:
                result.blit(surface, (x, height - surface.get_height()))
                x += surface.get_width()
            return result
        return self._render_text_plain(text, color, size)

    def _render_text_plain(self, text: str, color: tuple[int, ...], size: int = 24) -> pygame.Surface:
        """Render text using the bitmap font if available, else pygame font."""
        if self.bitmap_font is not None:
            try:
                # Add character spacing so bitmap text isn't cramped
                surface = self.bitmap_font.print(text, spacing=2)
                # Scale up tiny bitmap glyphs (8px tall) to a readable size
                target_height = max(size, 24)
                if surface.get_height() < target_height:
                    scale = target_height / surface.get_height()
                    new_width = max(1, int(surface.get_width() * scale))
                    surface = pygame.transform.scale(surface, (new_width, target_height))
                return surface
            except KeyError:
                pass
        font = self.title_font if size > 24 else self.font
        return font.render(text, True, color)

    def _format_slider_value(self, slider: Slider, value: float) -> str:
        """Format slider values compactly, using percentages for normalized controls."""
        if slider.min_value == 0.0 and slider.max_value == 1.0:
            return f"{round(value * 100):d}%"
        if abs(value - round(value)) < 1e-6:
            return str(int(round(value)))
        return f"{value:.2f}".rstrip("0").rstrip(".")

    def activate(self):
        item = self.items[self.selected]
        submenu = item.menu
        action = item.action
        if submenu is not None:
            self.app.open_menu(submenu)
        elif callable(action):
            action(self.app)
        elif action is not None:
            raise TypeError(f"Menu action for '{item.label}' must be callable")

    def _fit_matrix_to_screen(self, screen) -> pygame.Surface:
        """Resize the matrix in tile units, never by scaling rendered pixels."""
        margin = 16
        target_columns = max(3, (screen.get_width() - margin * 2) // TILE_SIZE)
        target_rows = max(3, (screen.get_height() - margin * 2) // TILE_SIZE)

        source_rows = len(self.definition.matrix)
        source_columns = len(self.definition.matrix[0])
        fitted = tuple(
            tuple(
                self.definition.matrix[
                    min(source_rows - 1, row * source_rows // target_rows)
                ][min(source_columns - 1, column * source_columns // target_columns)]
                for column in range(target_columns)
            )
            for row in range(target_rows)
        )
        return self.gui.render(
            fitted,
            self.colors,
            self.corner_type,
            self.edge_style,
        )

    def render(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        margin = 16
        panel_surface = self._fit_matrix_to_screen(screen)
        panel_rect = panel_surface.get_rect(center=screen.get_rect().center)
        screen.blit(panel_surface, panel_rect)

        title = self._render_text(self.title, (242, 246, 249), size=32)
        screen.blit(title, title.get_rect(midtop=(panel_rect.centerx, panel_rect.top + 13)))

        # Sliders occupy the main settings area, with actions anchored below them.
        self.slider_rects = []
        slider_y = panel_rect.top + 58
        for index, slider in enumerate(self.sliders):
            if slider_y + 44 > panel_rect.bottom - 48:
                break

            is_selected = self._is_slider_selected() and self._slider_index() == index
            is_active = self.active_slider == index
            if is_selected or is_active:
                colors = self.definition.selected_slider_colors
                label_color = (255, 255, 255)
            else:
                colors = self.definition.slider_colors
                label_color = (225, 232, 238)

            value_text = self._format_slider_value(slider, self.slider_values[index])
            label_text = f"{slider.label}: {value_text}"
            label_surface = self._render_text(label_text, label_color)
            screen.blit(label_surface, label_surface.get_rect(midtop=(panel_rect.centerx, slider_y)))

            track_width = max(240, min(int(panel_rect.width * 0.62), 560))
            track_x = panel_rect.centerx - track_width // 2
            track_y = slider_y + 22
            track_height = 8
            handle_size = 16

            hit_rect = pygame.Rect(track_x - 8, track_y - 4, track_width + 16, 16)
            self.slider_rects.append(hit_rect)
            track_rect = pygame.Rect(track_x, track_y, track_width, track_height)
            pygame.draw.rect(screen, colors[0], track_rect, border_radius=track_height // 2)

            position = self._slider_value_to_position(index)
            fill_width = int(track_width * position)
            if fill_width > 0:
                fill_rect = pygame.Rect(track_x, track_y, fill_width, track_height)
                pygame.draw.rect(screen, colors[1], fill_rect, border_radius=track_height // 2)

            handle_x = track_x + fill_width - handle_size // 2
            handle_y = track_y - (handle_size - track_height) // 2
            handle_rect = pygame.Rect(handle_x, handle_y, handle_size, handle_size)
            handle_color = colors[3] if (is_selected or is_active) else colors[2]
            pygame.draw.rect(screen, handle_color, handle_rect, border_radius=4)
            if is_selected or is_active:
                pygame.draw.rect(screen, (245, 248, 250), handle_rect, 2)

            slider_y += 46

        # Buttons are anchored at the bottom and use native tile-matrix sizes.
        self.button_rects = []
        button_y = panel_rect.bottom - 16
        for index in range(len(self.items) - 1, -1, -1):
            button_definition = self.items[index]
            surfaces = self.button_surfaces[index]
            button = surfaces[index == self.selected]
            rect = button.get_rect(midbottom=(panel_rect.centerx, button_y))
            screen.blit(button, rect)
            label = self._render_text(button_definition.label, (245, 248, 250), size=32)
            screen.blit(label, label.get_rect(center=rect.center))
            self.button_rects.insert(0, rect)
            button_y -= button.get_height() + 8