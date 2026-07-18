'''Game sound controller'''
import pygame
from scripts import reusable

class BGM:
    def __init__(self):
        pygame.mixer.init()

    def play(self, name):
        module = reusable.path_to_module(f"assets/audio/bgm/{name}.py")
        reusable.bytes_to_music(module.content)

class SFX:
    def __init__(self):
        pygame.mixer.init()
        
    def play(self, name):
        module = reusable.path_to_module(f"assets/audio/sfx/{name}.py")
        reusable.bytes_to_audio(module.content).play()

    def play_bytes(self, bytes):
        reusable.bytes_to_audio(bytes).play()
