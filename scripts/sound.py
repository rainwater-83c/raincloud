'''Game sound controller'''
import pygame
from . import reusable

class BGM:
    def __init__(self):
        pygame.mixer.init()

    def play(self, name):
        module = reusable.path_to_module(f"assets/audio/bgm/{name}.py")
        reusable.bytes_to_music(module.content)

class SFX:
    def __init__(self):
        pygame.mixer.init()
        
    def play(self, name, volume = (1.0, 1.0)):
        module = reusable.path_to_module(f"assets/audio/sfx/{name}.py")
        sound = reusable.bytes_to_audio(module.content).play()
        sound.set_volume(*volume)

    def play_bytes(self, bytes):
        reusable.bytes_to_audio(bytes).play()
