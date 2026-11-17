import math
import struct

import pygame


class GpuLightCompositor:
    def __init__(self, standalone=True):
        import moderngl

        self.moderngl = moderngl
        self.owns_context = standalone
        if standalone:
            try:
                self.context = moderngl.create_standalone_context(
                    require=330,
                    backend="egl",
                )
            except Exception:
                self.context = moderngl.create_standalone_context(require=330)
        else:
            self.context = moderngl.create_context(require=330)

        self.program = self.context.program(
            vertex_shader="""
                #version 330
                in vec2 in_position;
                in vec2 in_uv;
                out vec2 uv;

                void main() {
                    uv = in_uv;
                    gl_Position = vec4(in_position, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D scene_texture;
                uniform sampler2D filter_texture;
                uniform sampler2D source_texture;
                uniform sampler2D color_texture;
                uniform sampler2D overlay_texture;
                uniform int source_count;
                uniform int source_width;
                uniform int has_overlay;
                uniform int scene_bgra;
                uniform int scene_flip_y;
                uniform vec2 screen_size;
                uniform vec2 camera_offset;
                in vec2 uv;
                out vec4 fragment_color;

                void main() {
                    vec2 screen_position = vec2(
                        gl_FragCoord.x - 0.5,
                        screen_size.y - gl_FragCoord.y - 0.5
                    );
                    vec2 world_position = screen_position + camera_offset;
                    vec3 illumination = vec3(0.0);

                    for (int index = 0; index < source_count; index++) {
                        ivec2 source_coord = ivec2(
                            index % source_width,
                            index / source_width
                        );
                        vec4 source = texelFetch(source_texture, source_coord, 0);
                        vec3 color = texelFetch(color_texture, source_coord, 0).rgb;
                        float distance_to_source = distance(world_position, source.xy);
                        if (distance_to_source >= source.z) {
                            continue;
                        }

                        float ring = ceil(distance_to_source / source.z * 12.0) / 12.0;
                        float falloff = 1.0 - ring;
                        illumination += color * source.w * falloff * falloff;
                    }

                    vec2 scene_uv = vec2(
                        uv.x,
                        scene_flip_y != 0 ? 1.0 - uv.y : uv.y
                    );
                    vec4 scene_sample = texture(scene_texture, scene_uv);
                    vec3 scene = scene_bgra != 0
                        ? scene_sample.bgr
                        : scene_sample.rgb;
                    vec3 lit_scene = scene;
                    if (source_count > 0) {
                        vec3 filter_color = texture(filter_texture, uv).rgb;
                        lit_scene = clamp(
                            scene + illumination * filter_color,
                            0.0,
                            1.0
                        );
                    }
                    if (has_overlay != 0) {
                        vec4 overlay = texture(overlay_texture, uv);
                        lit_scene = mix(lit_scene, overlay.rgb, overlay.a);
                    }
                    fragment_color = vec4(
                        lit_scene,
                        1.0
                    );
                }
            """,
        )
        self.shadow_program = self.context.program(
            vertex_shader="""
                #version 330
                in vec4 in_caster;
                uniform vec2 world_size;
                uniform vec3 sun_vector;
                out vec4 caster_data;

                void main() {
                    float elevation = max(0.05, sun_vector.z);
                    vec2 offset = -sun_vector.xy * in_caster.z / elevation;
                    vec2 shadow_position = roundEven(in_caster.xy + offset);
                    vec2 clip_position = vec2(
                        2.0 * (shadow_position.x + 0.5) / world_size.x - 1.0,
                        1.0 - 2.0 * (shadow_position.y + 0.5) / world_size.y
                    );
                    gl_Position = vec4(clip_position, 0.0, 1.0);
                    gl_PointSize = 1.0;
                    caster_data = in_caster;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D geometry_texture;
                uniform sampler2D caster_mask;
                uniform vec2 world_size;
                uniform vec3 sun_vector;
                uniform float opacity_scale;
                in vec4 caster_data;
                out vec4 fragment_color;

                vec2 world_uv(vec2 point) {
                    return vec2(
                        (point.x + 0.5) / world_size.x,
                        1.0 - (point.y + 0.5) / world_size.y
                    );
                }

                void main() {
                    float elevation = max(0.05, sun_vector.z);
                    vec2 caster_position = caster_data.xy;
                    float caster_height = caster_data.z;
                    vec2 offset = -sun_vector.xy * caster_height / elevation;
                    vec2 shadow_position = vec2(
                        gl_FragCoord.x - 0.5,
                        world_size.y - gl_FragCoord.y - 0.5
                    );

                    vec4 receiver = texture(geometry_texture, world_uv(shadow_position));
                    if (receiver.a == 0.0 || receiver.r * 255.0 - 128.0 > caster_height + 0.01) {
                        discard;
                    }

                    vec2 raster_caster = roundEven(caster_position);
                    if (all(equal(shadow_position, raster_caster))
                        && texture(caster_mask, world_uv(shadow_position)).r > 0.5) {
                        discard;
                    }

                    int steps = int(ceil(max(abs(offset.x), abs(offset.y))));
                    for (int step = 1; step < steps; step++) {
                        float fraction = float(step) / float(steps);
                        vec2 ray_position = roundEven(caster_position + offset * fraction);
                        if (max(abs(ray_position.x - caster_position.x), abs(ray_position.y - caster_position.y)) <= 1.0) {
                            continue;
                        }
                        if (ray_position.x < 0.0 || ray_position.y < 0.0
                            || ray_position.x >= world_size.x || ray_position.y >= world_size.y) {
                            continue;
                        }
                        if (texture(caster_mask, world_uv(ray_position)).r > 0.5) {
                            continue;
                        }
                        vec4 occluder = texture(geometry_texture, world_uv(ray_position));
                        float ray_height = caster_height * (1.0 - fraction);
                        if (occluder.a > 0.0 && occluder.r * 255.0 - 128.0 > ray_height + 0.01) {
                            discard;
                        }
                    }

                    float alpha = (76.0 / 255.0) * opacity_scale * caster_data.w;
                    fragment_color = vec4(0.0, 0.0, 0.0, alpha);
                }
            """,
        )
        vertices = struct.pack(
                "24f",
            -1, -1, 0, 0,
            1, -1, 1, 0,
            -1, 1, 0, 1,
            -1, 1, 0, 1,
            1, -1, 1, 0,
            1, 1, 1, 1,
        )
        self.vertex_buffer = self.context.buffer(vertices)
        self.vertex_array = self.context.vertex_array(
            self.program,
            [(self.vertex_buffer, "2f 2f", "in_position", "in_uv")],
        )
        self.size = None
        self.source_size = None
        self.scene_texture = None
        self.filter_texture = None
        self.output_texture = None
        self.overlay_texture = None
        self.source_texture = None
        self.color_texture = None
        self.framebuffer = None
        self.shadow_size = None
        self.shadow_cache_key = None
        self.shadow_geometry_texture = None
        self.shadow_texture = None
        self.shadow_framebuffer = None
        self.shadow_groups = []

    def render(self, screen, filter_map, sources, camera, overlay=None):
        width, height = screen.get_size()
        self._ensure_frame_textures(width, height)
        bgra_masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
        raw_bgra = (
            screen.get_bytesize() == 4
            and screen.get_pitch() == width * 4
            and screen.get_masks() == bgra_masks
        )
        if raw_bgra:
            scene_view = screen.get_view("1")
            try:
                self.scene_texture.write(scene_view, alignment=1)
            finally:
                del scene_view
        else:
            self.scene_texture.write(pygame.image.tostring(screen, "RGBA", True))
        if filter_map is not None:
            self.filter_texture.write(pygame.image.tostring(filter_map, "RGBA", True))
        if overlay is not None:
            self.overlay_texture.write(pygame.image.tostring(overlay, "RGBA", True))

        active_sources = [
            source
            for source in sources
            if source["radius"] > 0
            and source["intensity"] > 0
            and any(source["color"])
        ]
        self._write_sources(active_sources, camera)

        self.scene_texture.use(0)
        self.filter_texture.use(1)
        self.source_texture.use(2)
        self.color_texture.use(3)
        self.overlay_texture.use(4)
        self.program["scene_texture"].value = 0
        self.program["filter_texture"].value = 1
        self.program["source_texture"].value = 2
        self.program["color_texture"].value = 3
        self.program["overlay_texture"].value = 4
        self.program["source_count"].value = len(active_sources)
        self.program["source_width"].value = self.source_size[0]
        self.program["has_overlay"].value = int(overlay is not None)
        self.program["scene_bgra"].value = int(raw_bgra)
        self.program["scene_flip_y"].value = int(raw_bgra)
        self.program["screen_size"].value = (width, height)
        self.program["camera_offset"].value = (
            camera.offset_x,
            camera.offset_y,
        )

        if self.owns_context:
            self.framebuffer.use()
        else:
            self.context.screen.use()
        self.context.viewport = (0, 0, width, height)
        self.context.disable(self.moderngl.BLEND | self.moderngl.DEPTH_TEST)
        self.vertex_array.render(mode=self.moderngl.TRIANGLES)
        if self.owns_context:
            pixels = self.framebuffer.read(components=4, alignment=1)
            screen.blit(
                pygame.image.fromstring(pixels, (width, height), "RGBA", True),
                (0, 0),
            )

    def render_sun_shadows(self, geometry, source_groups, sun):
        if sun[2] <= 0.05 or not source_groups:
            return None

        self._ensure_shadow_resources(geometry, source_groups)
        width, height = self.shadow_size
        self.shadow_framebuffer.use()
        self.context.viewport = (0, 0, width, height)
        self.shadow_framebuffer.clear(0.0, 0.0, 0.0, 0.0)
        self.context.enable(self.moderngl.BLEND)
        self.context.blend_equation = self.moderngl.MAX
        self.context.blend_func = (self.moderngl.ONE, self.moderngl.ONE)

        self.shadow_geometry_texture.use(0)
        self.shadow_program["geometry_texture"].value = 0
        self.shadow_program["world_size"].value = (width, height)
        self.shadow_program["sun_vector"].value = sun
        self.shadow_program["opacity_scale"].value = min(1.0, sun[2] / 0.45)

        for group in self.shadow_groups:
            if group["count"] == 0:
                continue
            group["mask"].use(1)
            self.shadow_program["caster_mask"].value = 1
            group["array"].render(mode=self.moderngl.POINTS)

        self.context.disable(self.moderngl.BLEND)
        pixels = self.shadow_framebuffer.read(components=4, alignment=1)
        return pygame.image.fromstring(pixels, (width, height), "RGBA", True)

    def prepare_sun_shadows(self, geometry, source_groups):
        if source_groups:
            self._ensure_shadow_resources(geometry, source_groups)

    def _ensure_shadow_resources(self, geometry, source_groups):
        width, height = geometry.get_size()
        cache_key = (id(geometry), id(source_groups), width, height)
        if self.shadow_cache_key == cache_key:
            return

        self._release_shadow_resources()
        self.shadow_size = (width, height)
        self.shadow_cache_key = cache_key
        geometry_data = pygame.image.tostring(geometry, "RGBA", True)
        self.shadow_geometry_texture = self.context.texture(
            (width, height),
            4,
            geometry_data,
            alignment=1,
        )
        self.shadow_geometry_texture.filter = (
            self.moderngl.NEAREST,
            self.moderngl.NEAREST,
        )
        self.shadow_texture = self.context.texture((width, height), 4)
        self.shadow_texture.filter = (
            self.moderngl.NEAREST,
            self.moderngl.NEAREST,
        )
        self.shadow_framebuffer = self.context.framebuffer(
            color_attachments=[self.shadow_texture]
        )

        self.shadow_groups = []
        for sources in source_groups:
            mask_data = bytearray(width * height)
            caster_data = []
            for pixel_x, pixel_y, caster_height, y_offset, depth, opacity in sources:
                if depth <= 0:
                    continue

                self._mark_caster_pixel(mask_data, width, height, pixel_x, pixel_y)
                for depth_index in range(depth):
                    caster_y = pixel_y + y_offset - depth_index
                    self._mark_caster_pixel(mask_data, width, height, pixel_x, caster_y)
                    if caster_height >= 0 and 0 <= caster_y < height:
                        caster_data.append((pixel_x, caster_y, caster_height, opacity))

            if caster_data:
                vertex_bytes = bytearray(len(caster_data) * 16)
                for index, caster in enumerate(caster_data):
                    struct.pack_into("4f", vertex_bytes, index * 16, *caster)
                vertex_buffer = self.context.buffer(vertex_bytes)
                vertex_array = self.context.vertex_array(
                    self.shadow_program,
                    [(vertex_buffer, "4f", "in_caster")],
                )
            else:
                vertex_buffer = None
                vertex_array = None

            mask_texture = self.context.texture(
                (width, height),
                1,
                mask_data,
                alignment=1,
            )
            mask_texture.filter = (
                self.moderngl.NEAREST,
                self.moderngl.NEAREST,
            )
            self.shadow_groups.append({
                "count": len(caster_data),
                "buffer": vertex_buffer,
                "array": vertex_array,
                "mask": mask_texture,
            })

    @staticmethod
    def _mark_caster_pixel(mask_data, width, height, pixel_x, pixel_y):
        if 0 <= pixel_x < width and 0 <= pixel_y < height:
            mask_data[(height - 1 - pixel_y) * width + pixel_x] = 255

    def _release_shadow_resources(self):
        for group in self.shadow_groups:
            if group["array"] is not None:
                group["array"].release()
            if group["buffer"] is not None:
                group["buffer"].release()
            group["mask"].release()
        self.shadow_groups = []
        if self.shadow_framebuffer is not None:
            self.shadow_framebuffer.release()
        for resource in (self.shadow_texture, self.shadow_geometry_texture):
            if resource is not None:
                resource.release()
        self.shadow_framebuffer = None
        self.shadow_texture = None
        self.shadow_geometry_texture = None
        self.shadow_size = None
        self.shadow_cache_key = None

    def _ensure_frame_textures(self, width, height):
        if self.size == (width, height):
            return

        self._release_frame_textures()
        texture_type = self.moderngl.NEAREST
        self.scene_texture = self.context.texture((width, height), 4)
        self.filter_texture = self.context.texture((width, height), 4)
        self.output_texture = self.context.texture((width, height), 4)
        self.overlay_texture = self.context.texture((width, height), 4)
        self.scene_texture.filter = (texture_type, texture_type)
        self.filter_texture.filter = (texture_type, texture_type)
        self.output_texture.filter = (texture_type, texture_type)
        self.overlay_texture.filter = (texture_type, texture_type)
        self.framebuffer = self.context.framebuffer(
            color_attachments=[self.output_texture]
        )
        self.size = (width, height)

    def _write_sources(self, sources, camera):
        maximum_width = self.context.info["GL_MAX_TEXTURE_SIZE"]
        count = max(1, len(sources))
        if count > maximum_width * maximum_width:
            raise ValueError("Too many light sources for the GPU texture")

        source_width = min(maximum_width, count)
        source_height = math.ceil(count / source_width)
        source_size = (source_width, source_height)
        if self.source_size != source_size:
            self._release_source_textures()
            self.source_texture = self.context.texture(
                source_size,
                4,
                dtype="f4",
            )
            self.color_texture = self.context.texture(
                source_size,
                4,
                dtype="f4",
            )
            self.source_size = source_size

        source_data = bytearray(source_width * source_height * 16)
        color_data = bytearray(source_width * source_height * 16)
        for index, source in enumerate(sources):
            struct.pack_into(
                "4f",
                source_data,
                index * 16,
                round(source["x"] - camera.offset_x) + camera.offset_x,
                round(source["y"] - camera.offset_y) + camera.offset_y,
                source["radius"],
                source["intensity"],
            )
            struct.pack_into(
                "4f",
                color_data,
                index * 16,
                *(channel / 255 for channel in source["color"]),
                1.0,
            )
        self.source_texture.write(source_data, alignment=1)
        self.color_texture.write(color_data, alignment=1)

    def _release_source_textures(self):
        for texture in (self.source_texture, self.color_texture):
            if texture is not None:
                texture.release()
        self.source_texture = None
        self.color_texture = None
        self.source_size = None

    def _release_frame_textures(self):
        if self.framebuffer is not None:
            self.framebuffer.release()
        for texture in (
            self.scene_texture,
            self.filter_texture,
            self.output_texture,
            self.overlay_texture,
        ):
            if texture is not None:
                texture.release()
        self.framebuffer = None
        self.scene_texture = None
        self.filter_texture = None
        self.output_texture = None
        self.overlay_texture = None
        self.size = None

    def close(self):
        self._release_frame_textures()
        self._release_source_textures()
        self._release_shadow_resources()
        self.vertex_array.release()
        self.vertex_buffer.release()
        self.program.release()
        self.shadow_program.release()
        if self.owns_context:
            self.context.release()