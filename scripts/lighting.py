import math
import warnings

import numpy as np
import pygame


class LightingSystem:
    def __init__(self, tilemap, use_gpu=False, gpu_compositor=None):
        self.tilemap = tilemap
        source_groups = getattr(tilemap, "shadow_source_groups", None)
        if source_groups:
            self._shadow_source_groups = source_groups
        elif tilemap.shadow_sources:
            self._shadow_source_groups = (tilemap.shadow_sources,)
        else:
            self._shadow_source_groups = ()
        self.use_gpu = use_gpu
        self._gpu_compositor = gpu_compositor
        self._gpu_failed = False
        self.light_sources = []
        self._glow_cache = {}
        self._sprite_map_cache = {}
        self._caster_pixel_cache = {}
        self._light_shadow_cache = {}
        self._shadow_phase = None
        self._shadow_surface = None
        self._receiver_height_geometry = None
        self._receiver_heights = None
        self._shadow_layer_surfaces = {}
        self._shadow_layer_rects = {}
        self._occlusion_geometry_source = None
        self._occlusion_geometry = None

    def add_light_source(
        self,
        x,
        y,
        color=(255, 180, 100),
        radius=48,
        intensity=0.2,
        height=None,
        casts_shadows=True,
    ):
        source = {
            "x": float(x),
            "y": float(y),
            "color": tuple(max(0, min(255, int(channel))) for channel in color),
            "radius": max(1.0, float(radius)),
            "intensity": max(0.0, min(1.0, float(intensity))),
            "height": float(height or self.tilemap.tileset.tile_size * 1.25),
            "casts_shadows": casts_shadows,
        }
        self.light_sources.append(source)
        return source

    def remove_light_source(self, source):
        self.light_sources.remove(source)

    def render_shadows(self, screen, camera, day_phase, render_list):
        sun = self._sun_vector(day_phase)
        if sun[2] <= 0.05:
            return {}

        dynamic_shadow_sources = []
        dynamic_shadow_geometry = []
        for _, entity in render_list:
            geometry = self._sprite_shadow_pixels(entity)
            if not geometry:
                continue
            dynamic_shadow_geometry.append((entity, geometry))
            entity_sources = [
                (
                    entity.rect.left + pixel_x,
                    entity.rect.top + pixel_y,
                    height,
                    y_offset,
                    depth,
                    opacity,
                )
                for pixel_x, pixel_y, height, y_offset, depth, opacity in geometry
            ]
            if entity_sources:
                dynamic_shadow_sources.append(entity_sources)

        shadow_surface = None
        gpu_shadows_rendered = False
        if self.tilemap.shadow_sources or dynamic_shadow_sources:
            compositor = self._get_gpu_compositor()
            if compositor is not None and not self._gpu_failed:
                try:
                    shadow_surface = compositor.render_sun_shadows(
                        self.tilemap.geometry_tiles,
                        self._shadow_source_groups,
                        sun,
                        dynamic_shadow_sources,
                        self._get_displaced_geometry(self.tilemap.geometry_tiles),
                    )
                    gpu_shadows_rendered = shadow_surface is not None
                except Exception as error:
                    self._gpu_failed = True
                    warnings.warn(
                        f"GPU sun shadows failed; using software shadows: {error}",
                        RuntimeWarning,
                        stacklevel=2,
                    )
            if shadow_surface is None and self.tilemap.shadow_sources:
                shadow_surface = self._sun_shadow_surface(day_phase)

        if not gpu_shadows_rendered and dynamic_shadow_geometry:
            if shadow_surface is None:
                shadow_surface = pygame.Surface(
                    (self.tilemap.width, self.tilemap.height),
                    pygame.SRCALPHA,
                )
            dynamic_shadows = pygame.Surface(
                (self.tilemap.width, self.tilemap.height),
                pygame.SRCALPHA,
            )
            for entity, geometry in dynamic_shadow_geometry:
                self._project_sources(
                    dynamic_shadows,
                    geometry,
                    entity.rect.left,
                    entity.rect.top,
                    sun,
                    self.tilemap.geometry_tiles,
                    0,
                    0,
                    self.tilemap.tileset.tile_size,
                    world_surface=True,
                )
            shadow_surface.blit(dynamic_shadows, (0, 0))

        if shadow_surface is None:
            return {}
        return self._split_shadow_surface(shadow_surface)

    def _split_shadow_surface(self, shadow_surface):
        shadow_rect = shadow_surface.get_bounding_rect()
        if not shadow_rect.width or not shadow_rect.height:
            return {}

        shadow_alpha = pygame.surfarray.array_alpha(
            shadow_surface.subsurface(shadow_rect)
        )
        shadow_pixels = shadow_alpha > 0
        if not np.any(shadow_pixels):
            return {}

        geometry = self._get_displaced_geometry(self.tilemap.geometry_tiles)
        if self._receiver_height_geometry is not geometry:
            self._receiver_heights = pygame.surfarray.array_red(geometry)
            self._receiver_height_geometry = geometry
            self._shadow_layer_surfaces.clear()
            self._shadow_layer_rects.clear()

        receiver_heights = self._receiver_heights[
            shadow_rect.left:shadow_rect.right,
            shadow_rect.top:shadow_rect.bottom,
        ]
        layers = {}
        for height in np.unique(receiver_heights[shadow_pixels]):
            surface = self._shadow_layer_surfaces.get(int(height))
            if surface is None:
                surface = pygame.Surface(shadow_surface.get_size(), pygame.SRCALPHA)
                self._shadow_layer_surfaces[int(height)] = surface
            previous_rect = self._shadow_layer_rects.get(int(height))
            if previous_rect is not None:
                previous_alpha = pygame.surfarray.pixels_alpha(
                    surface.subsurface(previous_rect)
                )
                previous_alpha.fill(0)
                del previous_alpha
            alpha_view = pygame.surfarray.pixels_alpha(
                surface.subsurface(shadow_rect)
            )
            alpha_view.fill(0)
            receiver_mask = receiver_heights == height
            alpha_view[receiver_mask] = shadow_alpha[receiver_mask]
            del alpha_view
            layers[int(height)] = surface
            self._shadow_layer_rects[int(height)] = shadow_rect
        return layers

    def render_lights(
        self,
        screen,
        camera,
        render_list,
        overlay=None,
        scene_ready=False,
        ambient_color=None,
    ):
        sources = list(self.tilemap.emission_sources) + self.light_sources
        for _, entity in render_list:
            for pixel_x, pixel_y, red, green, blue, strength in self._sprite_emission_pixels(entity):
                sources.append({
                    "x": entity.rect.left + pixel_x + 0.5,
                    "y": entity.rect.top + pixel_y + 0.5,
                    "color": (red, green, blue),
                    "intensity": strength * 0.18,
                    "radius": self.tilemap.tileset.tile_size * 1.25,
                })

        compositor = self._get_gpu_compositor()
        if not sources and compositor is None:
            return

        filter_map = None
        if sources:
            filter_map = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            filter_map.fill((255, 255, 255, 255))
            filter_map.blit(
                self.tilemap.filter_tiles,
                (-camera.offset_x, -camera.offset_y)
            )
            for _, entity in render_list:
                if not hasattr(entity, "spritesheet"):
                    continue
                image = entity.spritesheet.filter_surface(entity.direction, entity.frame)
                filter_map.blit(image, camera.apply(entity.rect))

        if compositor is not None and not self._gpu_failed:
            try:
                compositor.render(
                    screen,
                    filter_map,
                    sources,
                    camera,
                    overlay,
                    scene_ready=scene_ready,
                    ambient_color=ambient_color,
                )
                return
            except Exception as error:
                self._gpu_failed = True
                warnings.warn(
                    f"GPU lighting failed; using software lighting: {error}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        if sources:
            lightmap = pygame.Surface(screen.get_size())
            lightmap.fill((0, 0, 0))
            for source in sources:
                self._blit_glow(lightmap, source, camera, render_list)

            lightmap.blit(filter_map, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(lightmap, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        if compositor is not None:
            compositor.render(screen, None, [], camera, overlay)

    def _get_gpu_compositor(self):
        if not self.use_gpu:
            return None
        if self._gpu_compositor is not None or self._gpu_failed:
            return self._gpu_compositor
        if self._gpu_compositor is None:
            try:
                from .gpu_lighting import GpuLightCompositor

                self._gpu_compositor = GpuLightCompositor()
            except Exception as error:
                self._gpu_failed = True
                warnings.warn(
                    f"GPU lighting unavailable; using software lighting: {error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
        return self._gpu_compositor

    def close(self):
        if self._gpu_compositor is not None:
            self._gpu_compositor.close()
            self._gpu_compositor = None

    def prepare_sun_shadows(self):
        if not self._shadow_source_groups:
            return
        compositor = self._get_gpu_compositor()
        if compositor is None or self._gpu_failed:
            return

        try:
            compositor.prepare_sun_shadows(
                self.tilemap.geometry_tiles,
                self._shadow_source_groups,
                self._get_displaced_geometry(self.tilemap.geometry_tiles),
            )
        except Exception as error:
            self._gpu_failed = True
            warnings.warn(
                f"GPU sun-shadow setup failed; using software shadows: {error}",
                RuntimeWarning,
                stacklevel=2,
            )

    def _sun_vector(self, day_phase):
        angle = math.tau * (day_phase % 1.0) - math.pi / 2
        return (
            math.cos(angle),
            0,
            math.sin(angle),
        )

    def _get_displaced_geometry(self, geometry):
        if self._occlusion_geometry_source is geometry:
            return self._occlusion_geometry

        width, height = geometry.get_size()
        rgb = pygame.surfarray.array3d(geometry)
        alpha = pygame.surfarray.array_alpha(geometry)
        source_x, source_y = np.nonzero(alpha)
        displacement = 128 - rgb[source_x, source_y, 1]
        target_y = source_y + displacement
        valid = (target_y >= 0) & (target_y < height)
        heights = np.full((width, height), -1, dtype=np.int16)
        np.maximum.at(
            heights,
            (source_x[valid], target_y[valid]),
            rgb[source_x[valid], source_y[valid], 0],
        )

        displaced_geometry = pygame.Surface((width, height), pygame.SRCALPHA)
        rgb_view = pygame.surfarray.pixels3d(displaced_geometry)
        alpha_view = pygame.surfarray.pixels_alpha(displaced_geometry)
        rgb_view[:, :, 0] = np.maximum(heights, 0)
        alpha_view[:, :] = np.where(heights >= 0, 255, 0)
        del rgb_view, alpha_view

        self._occlusion_geometry_source = geometry
        self._occlusion_geometry = displaced_geometry
        return displaced_geometry

    def _sun_shadow_surface(self, day_phase):
        if not self.tilemap.shadow_sources:
            return None

        phase = day_phase % 1.0
        if self._shadow_phase == phase:
            return self._shadow_surface

        sun = self._sun_vector(phase)
        if sun[2] <= 0.05:
            self._shadow_phase = phase
            self._shadow_surface = None
            return None

        source_groups = self._shadow_source_groups
        shadow_surface = pygame.Surface(
            (self.tilemap.width, self.tilemap.height),
            pygame.SRCALPHA,
        )
        for sources in source_groups:
            self._project_sources(
                shadow_surface,
                sources,
                0,
                0,
                sun,
                self.tilemap.geometry_tiles,
                0,
                0,
                self.tilemap.tileset.tile_size,
                world_surface=True,
            )
        self._shadow_phase = phase
        self._shadow_surface = shadow_surface
        return shadow_surface

    def _project_sources(
        self,
        target,
        sources,
        origin_x,
        origin_y,
        sun,
        world_geometry,
        camera_x,
        camera_y,
        tile_size,
        world_surface=False,
        caster_pixels=None,
        projected_points=None,
        draw_all_points=True,
    ):
        sun_x, sun_y, sun_height = sun
        elevation = max(0.05, sun_height)
        opacity_scale = min(1.0, sun_height / 0.45)
        target_width, target_height = target.get_size()
        world_width = world_geometry.get_width()
        world_height = world_geometry.get_height()
        occlusion_geometry = self._get_displaced_geometry(world_geometry)
        if projected_points is None:
            projected_points = {}
        new_projected_points = set()

        # The geometry pixels for a spritesheet frame do not change as the
        # entity moves. Cache them in source-local coordinates so we don't
        # rebuild a potentially large set on every frame.
        if caster_pixels is None:
            caster_pixels = self._get_caster_pixels(sources)
        for pixel_x, pixel_y, height, y_offset, depth, caster_opacity in sources:
            if height < 0 or depth <= 0:
                continue

            alpha = round(76 * opacity_scale * caster_opacity)
            if alpha <= 0:
                continue

            for depth_index in range(depth):
                if height < 0:
                    continue

                world_x = origin_x + pixel_x
                world_y = origin_y + pixel_y + y_offset
                caster_x = world_x
                caster_y = world_y - depth_index
                offset_x = -sun_x * height / elevation
                offset_y = -sun_y * height / elevation
                shadow_x = round(caster_x + offset_x)
                shadow_y = round(caster_y + offset_y)

                if world_surface:
                    local_x, local_y = shadow_x, shadow_y
                else:
                    local_x = shadow_x - camera_x
                    local_y = shadow_y - camera_y

                if not (0 <= local_x < target_width and 0 <= local_y < target_height):
                    continue
                if not (0 <= shadow_x < world_width and 0 <= shadow_y < world_height):
                    continue

                steps = max(1, math.ceil(max(abs(offset_x), abs(offset_y))))
                blocked = False
                for step in range(1, steps):
                    fraction = step / steps
                    ray_x = round(caster_x + offset_x * fraction)
                    ray_y = round(caster_y + offset_y * fraction)
                    if max(abs(ray_x - caster_x), abs(ray_y - caster_y)) <= 1:
                        continue
                    if (ray_x - origin_x, ray_y - origin_y) in caster_pixels:
                        continue
                    if not (0 <= ray_x < world_width and 0 <= ray_y < world_height):
                        continue
                    occluder = occlusion_geometry.get_at((ray_x, ray_y))
                    ray_height = height * (1 - fraction)
                    if occluder.a and occluder.r - 128 > ray_height:
                        blocked = True
                        break
                if blocked:
                    continue

                receiver = occlusion_geometry.get_at((shadow_x, shadow_y))
                if receiver.a == 0 or receiver.r - 128 > height:
                    continue

                target.set_at((local_x, local_y), (0, 0, 0, alpha))
                point = (local_x, local_y, alpha)
                key = (pixel_x, pixel_y, depth_index)
                previous = projected_points.get(key)
                if previous is None or alpha > previous[2]:
                    projected_points[key] = point
                new_projected_points.add(key)

        line_keys = projected_points if draw_all_points else new_projected_points
        for source_x, source_y, depth_index in line_keys:
            start = projected_points[(source_x, source_y, depth_index)]
            start_x, start_y, start_alpha = start
            neighbors = [
                (source_x + 1, source_y, depth_index),
                (source_x, source_y + 1, depth_index),
                (source_x, source_y, depth_index + 1),
            ]
            if not draw_all_points:
                neighbors.extend((
                    (source_x - 1, source_y, depth_index),
                    (source_x, source_y - 1, depth_index),
                    (source_x, source_y, depth_index - 1),
                ))
            for neighbor in neighbors:
                if not draw_all_points and (source_x, source_y, depth_index) > neighbor:
                    continue
                end = projected_points.get(neighbor)
                if end is None:
                    continue
                end_x, end_y, end_alpha = end
                pygame.draw.line(
                    target,
                    (0, 0, 0, min(start_alpha, end_alpha)),
                    (start_x, start_y),
                    (end_x, end_y),
                )

    def _get_caster_pixels(self, sources):
        cache_key = id(sources)
        cached_caster_data = self._caster_pixel_cache.get(cache_key)
        if cached_caster_data is not None and cached_caster_data[0] is sources:
            return cached_caster_data[1]

        caster_pixels = set()
        for pixel_x, pixel_y, _, y_offset, depth, _ in sources:
            if depth <= 0:
                continue
            caster_pixels.add((pixel_x, pixel_y))
            for depth_index in range(depth):
                caster_pixels.add((
                    pixel_x,
                    pixel_y + y_offset - depth_index,
                ))
        self._caster_pixel_cache[cache_key] = (sources, caster_pixels)
        if len(self._caster_pixel_cache) > 256:
            self._caster_pixel_cache.clear()
            self._caster_pixel_cache[cache_key] = (sources, caster_pixels)
        return caster_pixels

    def _sprite_shadow_pixels(self, entity):
        if not hasattr(entity, "spritesheet"):
            return ()
        key = (id(entity.spritesheet), entity.direction, entity.frame)
        if key not in self._sprite_map_cache:
            image = entity.spritesheet.geometry_surface(entity.direction, entity.frame)
            pixels = []
            for y in range(image.get_height()):
                for x in range(image.get_width()):
                    red, green, blue, alpha = image.get_at((x, y))
                    if alpha and red >= 128 and blue > 0:
                        pixels.append((x, y, red - 128, 128 - green, blue, alpha / 255))
            self._sprite_map_cache[key] = tuple(pixels)
        return self._sprite_map_cache[key]

    def _sprite_emission_pixels(self, entity):
        if not hasattr(entity, "spritesheet"):
            return ()
        key = (id(entity.spritesheet), entity.direction, entity.frame, "emission")
        if key not in self._sprite_map_cache:
            image = entity.spritesheet.emission_surface(entity.direction, entity.frame)
            pixels = []
            for y in range(image.get_height()):
                for x in range(image.get_width()):
                    red, green, blue, alpha = image.get_at((x, y))
                    if alpha and (red or green or blue):
                        pixels.append((x, y, red, green, blue, alpha / 255))
            self._sprite_map_cache[key] = tuple(pixels)
        return self._sprite_map_cache[key]

    def _blit_glow(self, lightmap, source, camera, render_list):
        radius = round(source["radius"])
        color = source["color"]
        intensity = source["intensity"]
        if radius <= 0 or intensity <= 0 or not any(color):
            return

        key = (radius, color, round(intensity, 3))
        glow = self._glow_cache.get(key)
        if glow is None:
            diameter = radius * 2 + 1
            glow = pygame.Surface((diameter, diameter))
            glow.fill((0, 0, 0))
            center = (radius, radius)
            for ring in range(12, -1, -1):
                fraction = ring / 12
                falloff = (1 - fraction) ** 2
                ring_color = tuple(
                    round(channel * intensity * falloff)
                    for channel in color
                )
                pygame.draw.circle(
                    glow,
                    ring_color,
                    center,
                    round(radius * fraction)
                )
            self._glow_cache[key] = glow

        if source.get("casts_shadows", True):
            shadow_points = self._point_light_shadow_points(source, render_list)
            if shadow_points:
                glow = glow.copy()
                for shadow_x, shadow_y in shadow_points:
                    glow.set_at((shadow_x, shadow_y), (0, 0, 0))

        position = (
            round(source["x"] - camera.offset_x) - radius,
            round(source["y"] - camera.offset_y) - radius,
        )
        lightmap.blit(glow, position, special_flags=pygame.BLEND_RGB_ADD)

    def _point_light_shadow_points(self, light, render_list):
        dynamic_state = tuple(
            (
                id(entity),
                entity.rect.left,
                entity.rect.top,
                getattr(entity, "direction", 0),
                getattr(entity, "frame", 0),
            )
            for _, entity in render_list
        )
        key = (
            round(light["x"], 2),
            round(light["y"], 2),
            round(light["radius"], 2),
            round(light["height"], 2),
            dynamic_state,
        )
        cached = self._light_shadow_cache.get(key)
        if cached is not None:
            return cached

        radius = light["radius"]
        light_x = light["x"]
        light_y = light["y"]
        tile_size = self.tilemap.tileset.tile_size
        min_cell_x = max(0, int((light_x - radius) // tile_size))
        max_cell_x = min(self.tilemap.width // tile_size, int((light_x + radius) // tile_size) + 1)
        min_cell_y = max(0, int((light_y - radius) // tile_size))
        max_cell_y = min(self.tilemap.height // tile_size, int((light_y + radius) // tile_size) + 1)
        casters = []
        for cell_y in range(min_cell_y, max_cell_y + 1):
            for cell_x in range(min_cell_x, max_cell_x + 1):
                casters.extend(self.tilemap.shadow_grid.get((cell_x, cell_y), ()))

        for _, entity in render_list:
            for pixel_x, pixel_y, height, y_offset, depth, opacity in self._sprite_shadow_pixels(entity):
                casters.append((
                    entity.rect.left + pixel_x,
                    entity.rect.top + pixel_y,
                    height,
                    y_offset,
                    depth,
                    opacity,
                ))

        casters = (
            (
                caster_x,
                caster_y + y_offset - depth_index,
                caster_height,
                0,
                1,
                opacity,
            )
            for caster_x, caster_y, caster_height, y_offset, depth, opacity in casters
            for depth_index in range(depth)
        )

        glow_radius = round(radius)
        shadow_points = set()
        light_height = light["height"]
        for caster_x, caster_y, caster_height, _, _, opacity in casters:
            if caster_height <= 0 or light_height <= caster_height:
                continue

            offset_x = caster_x - light_x
            offset_y = caster_y - light_y
            distance = math.hypot(offset_x, offset_y)
            if distance >= radius:
                continue

            blocked = False
            steps = max(1, math.ceil(distance))
            for step in range(1, steps):
                fraction = step / steps
                ray_x = round(light_x + offset_x * fraction)
                ray_y = round(light_y + offset_y * fraction)
                if not (0 <= ray_x < self.tilemap.width and 0 <= ray_y < self.tilemap.height):
                    continue
                occluder = self.tilemap.geometry_tiles.get_at((ray_x, ray_y))
                ray_height = light_height * (1 - fraction)
                if occluder.a and occluder.r - 128 >= ray_height:
                    blocked = True
                    break
            if blocked:
                continue

            projection = caster_height / (light_height - caster_height)
            shadow_x = caster_x + offset_x * projection
            shadow_y = caster_y + offset_y * projection
            local_x = round(shadow_x - light_x + glow_radius)
            local_y = round(shadow_y - light_y + glow_radius)
            if not (0 <= local_x < glow_radius * 2 + 1 and 0 <= local_y < glow_radius * 2 + 1):
                continue

            if not (0 <= round(shadow_x) < self.tilemap.width and 0 <= round(shadow_y) < self.tilemap.height):
                continue
            receiver = self.tilemap.geometry_tiles.get_at((round(shadow_x), round(shadow_y)))
            if receiver.a == 0 or receiver.r - 128 >= caster_height:
                continue

            falloff = (1 - distance / radius) ** 2
            if falloff * opacity > 0.02:
                shadow_points.add((local_x, local_y))

        result = tuple(shadow_points)
        self._light_shadow_cache[key] = result
        if len(self._light_shadow_cache) > 512:
            self._light_shadow_cache.clear()
        return result