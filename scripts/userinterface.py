'''UI texture generation and menu controller.'''

import io
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
class Menu:
    title: str
    matrix: Matrix
    buttons: tuple[Button, ...]
    colors: Palette
    corner_type: str = "rounded"
    edge_style: str = "straight"
    button_matrix: Matrix = (
        (1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1),
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

        self.selected = 0
        self.gui = GUITexture()
        self.corner_type = self.definition.corner_type
        self.edge_style = self.definition.edge_style
        self.colors = self.definition.colors
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
                    self.selected = (self.selected - 1) % len(self.items)
                elif action == "down":
                    self.selected = (self.selected + 1) % len(self.items)
                elif action == "confirm":
                    self.activate()
                elif action == "deny":
                    self.app.close_menu()
                else:
                    continue
                return True

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
                    self.selected = (self.selected - 1) % len(self.items)
                elif action == "down":
                    self.selected = (self.selected + 1) % len(self.items)
                elif action == "confirm":
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

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    self.activate()
                    return True

        return False

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

    def render(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        panel_rect = self.panel_surface.get_rect(center=screen.get_rect().center)
        screen.blit(self.panel_surface, panel_rect)

        title = self.title_font.render(self.title, True, (242, 246, 249))
        screen.blit(title, title.get_rect(midtop=(panel_rect.centerx, panel_rect.top + 13)))

        self.button_rects = []
        button_y = panel_rect.top + 64
        for index, (button_definition, surfaces) in enumerate(zip(self.items, self.button_surfaces)):
            button = surfaces[index == self.selected]
            if button_y + button.get_height() > panel_rect.bottom - 16:
                break
            rect = button.get_rect(midtop=(panel_rect.centerx, button_y))
            screen.blit(button, rect)
            label = self.font.render(button_definition.label, True, (245, 248, 250))
            screen.blit(label, label.get_rect(center=rect.center))
            self.button_rects.append(rect)
            button_y += button.get_height() + 8