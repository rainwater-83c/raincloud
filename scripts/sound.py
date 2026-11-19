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
        self._modules = {}
        self._sounds = {}

    def _sound(self, key, audio_data):
        sound = self._sounds.get(key)
        if sound is None:
            sound = reusable.bytes_to_audio(audio_data)
            self._sounds[key] = sound
        return sound
       
    def play(self, name, volume = (1.0, 1.0)):
        module = self._modules.get(name)
        if module is None:
            module = reusable.path_to_module(Path(f"assets/audio/sfx/{name}.py"))
            self._modules[name] = module
        channel = self._sound(("name", name), module.audio).play()
        if channel is not None:
            channel.set_volume(*volume)
        return channel

    def play_bytes(self, audio_data, volume=(1.0, 1.0)):
        channel = self._sound(("bytes", audio_data), audio_data).play()
        if channel is not None:
            channel.set_volume(*volume)
        return channel
