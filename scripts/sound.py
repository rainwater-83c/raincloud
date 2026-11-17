'''Game sound controller'''
import pygame
from pathlib import Path
from . import reusable

class BGM:
    def __init__(self):
        pygame.mixer.init()

    def play(self, name, module=None):
        """Load and play a background music track, looping indefinitely."""
        if module is None:
            if name is None:
                raise ValueError("Tilemap requires a module or asset name")
            module = __import__(f"assets.bgm.{name}", fromlist=[name])
        reusable.bytes_to_music(module.audio)
        pygame.mixer.music.play(-1)

    def stop(self):
        """Stop the currently playing background music."""
        pygame.mixer.music.stop()

    def set_volume(self, volume: float) -> None:
        """Set BGM volume (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

class SFX:
    def __init__(self):
        pygame.mixer.init()
       
    def play(self, name, volume = (1.0, 1.0)):
        module = reusable.path_to_module(Path(f"assets/audio/sfx/{name}.py"))
        sound = reusable.bytes_to_audio(module.audio).play()
        sound.set_volume(*volume)

    def play_bytes(self, bytes):
        reusable.bytes_to_audio(bytes).play()
