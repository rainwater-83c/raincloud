'''The main script. This is where the code for the event loop goes.'''

import pygame
from pygame.locals import *
import sys
import warnings
from .tilemap import Tilemap
from . import sprite, sound, save
from .font import Font
from .lighting import LightingSystem
from .userinterface import MenuController


__version__ = "0.0.0 PT"

class Camera:
    '''The main camera object.'''
    def __init__(self, width:int, height: int):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0

    def apply(self, rect: pygame.Rect):
        return rect.move(-self.offset_x, -self.offset_y)

    def update(self, target: sprite.Sprite, screen_w: int, screen_h: int):
        self.offset_x = target.x - screen_w // 2
        self.offset_y = target.y - screen_h // 2

        self.offset_x = max(0, min(self.offset_x, self.width - screen_w))
        self.offset_y = max(0, min(self.offset_y, self.height - screen_h))
        return self

class App:
    '''The main app.'''
    def __init__(self, tilemap: Tilemap, core_assets, settings):
        pygame.init()

        self.settings = settings
        core_assets = core_assets or {}
        font_asset = core_assets.get("font")
        self.bitmap_font = Font(font_asset) if font_asset is not None else None
        icon_module = core_assets.get("icon")
        icon_texture = getattr(icon_module, "texture", None)
        if icon_texture is not None:
            icon_image = pygame.image.load(__import__("io").BytesIO(icon_texture))
            pygame.display.set_icon(icon_image)
        pygame.display.set_caption(self.settings.WINDOW_TITLE)
        flags = RESIZABLE if self.settings.WINDOW_RESIZABLE else 0
        gpu_compositor = None
        self.gpu_display = False
        if getattr(self.settings, "GPU_LIGHTING", False):
            try:
                pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
                pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
                pygame.display.gl_set_attribute(
                    pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
                )
                pygame.display.gl_set_attribute(
                    pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True
                )
                pygame.display.set_mode(
                    self.settings.WINDOW_SIZE,
                    flags | OPENGL | DOUBLEBUF,
                )
                from .gpu_lighting import GpuLightCompositor

                gpu_compositor = GpuLightCompositor(standalone=False)
                self.gpu_display = True
                self.screen = pygame.Surface(
                    self.settings.WINDOW_SIZE,
                    pygame.SRCALPHA,
                )
            except Exception as error:
                if gpu_compositor is not None:
                    gpu_compositor.close()
                warnings.warn(
                    f"OpenGL display unavailable; using Pygame software display: {error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                self.screen = pygame.display.set_mode(
                    self.settings.WINDOW_SIZE,
                    flags,
                )
        else:
            self.screen = pygame.display.set_mode(self.settings.WINDOW_SIZE, flags)
        self.ambient_overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.running = False
        self.keybinds = {}
        self.gamepad_keybinds = {}
        self.pressed_keys = []  # blank list for held keys
        self.tilemap = tilemap
        self.tilemap.app = self
        self.core_assets = core_assets
        self.dialogue_box = None
        self.dialogue_fonts = {}
        if self.bitmap_font is not None:
            self.dialogue_fonts["font"] = self.bitmap_font
        for font_name, font_asset in self.core_assets.items():
            if font_name == "font":
                continue
            if callable(getattr(font_asset, "get_glyph", None)) or callable(
                getattr(font_asset, "print", None)
            ):
                self.dialogue_fonts[font_name] = font_asset
        self.menu_definitions = {}
        sprite_module = self.core_assets.get("sprites")
        sprite_definitions = getattr(sprite_module, "sprites", None)
        if not sprite_definitions or "player" not in sprite_definitions:
            raise ValueError("Core sprites asset must define a 'player' sprite")
        self.lighting = LightingSystem(
            self.tilemap,
            use_gpu=self.gpu_display,
            gpu_compositor=gpu_compositor,
        )
        self.lighting.prepare_sun_shadows()
        self.camera = Camera(self.tilemap.width, self.tilemap.height)
        self.party = sprite.Party()
        self.player = sprite_definitions['player'](self.tilemap)
        self.player.app = self
        self.party.leader = self.player
        self.sprites = [self.player]
        for row in self.tilemap.tile_sprites:
            for tile_sprite in row:
                if tile_sprite is not None:
                    tile_sprite.app = self
        self.clock = pygame.time.Clock()
        self.joystick = (
            pygame.joystick.Joystick(0)
            if pygame.joystick.get_count()
            else None
        )
        self.script = None
        self.just_pressed = []
        self.menu = None
        self.fps = 0
        self.save = save.Save()
        self.master_volume = 1.0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self.frame_times = []
        self.max_tracked_frames = self.settings.FPS_HISTORY
        self.bgm = sound.BGM()
        self.sfx = sound.SFX()
        self.font = pygame.font.SysFont(
            self.settings.DEBUG_FONT_NAME,
            self.settings.DEBUG_FONT_SIZE,
        )
        self.events = {}
        self.keys = {}
        self.oncekeys = {}
        self.time = 0
        self.day_length = self.tilemap.module.day_length
        self.day_phase = 0
        self.phase_colors = self.tilemap.module.phase_colors

        # Play background music if the tilemap defines one
        bgm_name = getattr(self.tilemap.module, "bgm", None)
        if bgm_name:
            self.bgm.play(bgm_name)
            self.bgm.set_volume(self.master_volume * self.music_volume)

    def add_light_source(self, x, y, color=(255, 180, 100), radius=48, intensity=0.2, height=None, casts_shadows=True):
        return self.lighting.add_light_source(
            x, y, color, radius, intensity, height, casts_shadows
        )

    def open_menu(self, name: str):
        definitions = self.menu_definitions or None
        self.menu = MenuController(name, self, definitions)
        return self.menu

    def close_menu(self):
        self.menu = None

    # function is defined with _ at the start to show that this function isnt meant to be used out of this class

    def handle_events(self):
        menu_was_open = self.menu is not None
        for event in pygame.event.get():
            if self.menu is not None and event.type != QUIT:
                if self.menu.handle_event(event):
                    continue
            handler = self.events.get(event.type)
            if handler:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EVENT ERROR] {e}")

        if menu_was_open or self.menu is not None:
            return

        for key, value in self.keys.items():
            if key in self.pressed_keys:
                value()
        for key, value in self.oncekeys.items():
            if key in self.just_pressed:
                value()

    def handle_entities(self, dt: float):
        self.player.update(dt, self.player.speed*2 if not 'run' in self.pressed_keys else self.player.speed)

        # IMPORTANT:
        # rect MUST follow world position
        self.player.rect.midbottom = (
            self.player.x,
            self.player.y + round(self.player.displacement),
        )

        self.camera.update(
            self.player,
            self.screen.get_width(),
            self.screen.get_height()
        )

        if self.script:
            try:
                next(self.script)
            except StopIteration:
                self.script = None

    def render(self):
        if self.gpu_display:
            window_size = pygame.display.get_window_size()
            if self.screen.get_size() != window_size:
                self.screen = pygame.Surface(window_size, pygame.SRCALPHA)
                self.ambient_overlay = pygame.Surface(window_size, pygame.SRCALPHA)

        self.screen.fill((0, 0, 0))

        # Ground layer
        #self.screen.blit(
        #    self.tilemap.ground_tiles,
        #    (-self.camera.offset_x, -self.camera.offset_y)
        #)
        layers_by_height = {}
        render_list = sorted(
            ((entity.rect.bottom, entity) for entity in self.sprites),
            key=lambda item: item[0],
        )
        shadow_layers = self.lighting.render_shadows(
            self.screen,
            self.camera,
            self.day_phase,
            render_list,
        )

        for height, surface in self.tilemap.height_layers.items():
            layers_by_height.setdefault(height, []).append((None, surface))
        for height, surface in shadow_layers.items():
            layers_by_height.setdefault(height, []).append((None, surface))
        for spr in self.sprites:
            for height, surface in spr.split().items():
                layers_by_height.setdefault(height, []).append((spr, surface))

        shadow_surface_ids = {id(surface) for surface in shadow_layers.values()}
        gpu_layers = []
        for height in sorted(layers_by_height):
            for spr, surface in layers_by_height[height]:
                if spr is None:
                    pos = (-self.camera.offset_x, -self.camera.offset_y)
                else:
                    pos = self.camera.apply(spr.rect)
                gpu_layers.append((surface, pos, id(surface) in shadow_surface_ids))

        gpu_scene_ready = False
        if self.gpu_display:
            compositor = self.lighting._get_gpu_compositor()
            if compositor is not None and not self.lighting._gpu_failed:
                try:
                    compositor.render_scene(gpu_layers, self.screen.get_size())
                    gpu_scene_ready = True
                except Exception as error:
                    warnings.warn(
                        f"GPU scene rendering failed; using Pygame composition: {error}",
                        RuntimeWarning,
                        stacklevel=2,
                    )

        if not gpu_scene_ready:
            for surface, pos, _ in gpu_layers:
                self.screen.blit(surface, pos)

        phase = self.day_phase % 1.0

        for (start_phase, start), (end_phase, end) in zip(
            self.phase_colors, self.phase_colors[1:]
        ):
            if start_phase <= phase < end_phase:
                t = (phase - start_phase) / (end_phase - start_phase)
                t = 6 * t**5 - 15 * t**4 + 10 * t**3
                color = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
                break

        if self.ambient_overlay.get_size() != self.screen.get_size():
            self.ambient_overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.ambient_overlay.fill(color)

        if not gpu_scene_ready:
            self.screen.blit(self.ambient_overlay, (0,0))
        if self.gpu_display:
            menu_overlay = None
            if self.menu is not None or self.dialogue_box is not None:
                menu_overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                if self.menu is not None:
                    self.menu.render(menu_overlay)
                if self.dialogue_box is not None:
                    self.dialogue_box.render(menu_overlay)
            self.lighting.render_lights(
                self.screen,
                self.camera,
                render_list,
                overlay=menu_overlay,
                scene_ready=gpu_scene_ready,
                ambient_color=color if gpu_scene_ready else None,
            )
        else:
            self.lighting.render_lights(self.screen, self.camera, render_list)
            if self.menu is not None:
                self.menu.render(self.screen)
            if self.dialogue_box is not None:
                self.dialogue_box.render(self.screen)
        pygame.display.flip()

    def tick(self):
        print(self.player.height, self.player.displacement)
        self.time = (self.time + 1) % self.day_length
        self.day_phase = self.time / self.day_length
        self.just_pressed.clear()
        dt = self.clock.tick(self.settings.TARGET_FPS) / 1000.0
        if dt > 0:
            self.frame_times.append(dt)
        if len(self.frame_times) > self.max_tracked_frames:
            self.frame_times.pop(0)

        if self.frame_times:
            avg_dt = sum(self.frame_times) / len(self.frame_times)
            self.fps = 1 / avg_dt
        else:
            self.fps = 0

        self.handle_events()
        self.handle_entities(dt)
        self.render()

    def run(self):
        self.running = True
        try:
            while self.running:
                self.tick()
        finally:
            self.lighting.close()

        pygame.mixer.quit()
        pygame.display.quit()
        pygame.quit()
        
