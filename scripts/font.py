"""Compose bitmap-font glyphs into text surfaces."""

import pygame


class Font:
    """Render strings using the configured font asset."""

    def __init__(self, font_asset):
        self.symbol_to_index = font_asset.SYMBOL_TO_INDEX
        self.font_asset = font_asset
        self.line_height = font_asset.box_size

    def print(
        self,
        text: str,
        spacing: int = 0,
        space_length: int = 4,
    ) -> pygame.Surface:
        """Render text as a transparent surface using the configured glyphs."""
        if spacing < 0 or space_length < 0:
            raise ValueError("spacing and space_length must not be negative")

        glyphs = []
        for character in text:
            if character not in self.symbol_to_index:
                raise KeyError(f"Unsupported font character: {character!r}")
            glyph_index = self.symbol_to_index[character]
            glyphs.append(
                None if character == " " else self.font_asset.get_glyph(glyph_index)
            )

        if not glyphs:
            return pygame.Surface((1, self.line_height), pygame.SRCALPHA, 32)

        advances = [
            space_length if glyph is None else glyph.get_width()
            for glyph in glyphs
        ]
        width = sum(advances) + spacing * (len(glyphs) - 1)
        text_surface = pygame.Surface(
            (max(width, 1), self.line_height), pygame.SRCALPHA, 32
        )
        x = 0
        for glyph, advance in zip(glyphs, advances):
            if glyph is not None:
                text_surface.blit(
                    glyph,
                    (x, self.line_height - glyph.get_height()),
                )
            x += advance + spacing
        return text_surface

    def set_palette(self, white, black=(0, 0, 0, 0)) -> None:
        """Change the font's white and black colors."""
        self.font_asset.set_palette(white, black)