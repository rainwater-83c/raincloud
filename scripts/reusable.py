'''Reusable code for other scripts.'''

import pygame
import io
import importlib.util
import sys
import pathlib

__version__ = "0.0.0 PT"

def bytes_to_image(bytes):
    image_stream = io.BytesIO(bytes)
    image_surface = pygame.image.load(image_stream)
    return image_surface

def module_image(module, attribute, size, default_color):
    image_bytes = getattr(module, attribute, None)
    if image_bytes is None:
        image = pygame.Surface(size, pygame.SRCALPHA)
        image.fill(default_color)
        return image

    image = bytes_to_image(image_bytes)
    if image.get_size() != size:
        raise ValueError(
            f"{attribute} map size {image.get_size()} does not match texture size {size}"
        )
    return image

def bytes_to_music(bytes):
    audio_stream = io.BytesIO(bytes)
    audio = pygame.mixer.music.load(audio_stream)
    return audio

def bytes_to_audio(bytes):
    audio_stream = io.BytesIO(bytes)
    audio = pygame.mixer.Sound(audio_stream)
    return audio

def path_to_module(path, format):
    module_name = path.stem
    file_path = path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    temp_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = temp_module
    spec.loader.exec_module(temp_module)
    return temp_module