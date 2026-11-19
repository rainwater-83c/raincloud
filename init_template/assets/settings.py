"""Settings menu definition and volume controls for Raincloud games."""

from raincloud.scripts.userinterface import Button, Menu, Slider, Matrix

def filled_matrix(width, height) -> Matrix:
	return tuple(tuple(1 for _ in range(width)) for _ in range(height))

def apply_master_volume(app, value: float) -> None:
    """Apply master volume as a multiplier to music and SFX."""
    app.master_volume = value
    music = getattr(app, "music_volume", 1.0)
    try:
        app.bgm.set_volume(min(1.0, value * music))
    except Exception:
        pass


def apply_music_volume(app, value: float) -> None:
    """Apply music volume, combined with master volume."""
    app.music_volume = value
    master = getattr(app, "master_volume", 1.0)
    try:
        app.bgm.set_volume(min(1.0, master * value))
    except Exception:
        pass


def apply_sfx_volume(app, value: float) -> None:
    """Store SFX volume on the app for SFX playback to use."""
    app.sfx_volume = value


def back_to_main(app) -> None:
    """Close Settings and return to the menu that opened it."""
    app.close_menu()


DEFAULT_MASTER_VOLUME = 1.0
DEFAULT_MUSIC_VOLUME = 1.0
DEFAULT_SFX_VOLUME = 1.0
SLIDER_TRACK_WIDTH = 200

MENUS = {
    "settings": Menu(
        title="Settings",
        matrix=filled_matrix(13, 16),
        colors=(
            (255, 255, 255, 0),
            (0, 192, 192, 255),
            (0, 192, 192, 255),
            (0, 255, 255, 255),
            (0, 255, 255, 255),
            (0, 255, 255, 255),
            (0, 128, 128, 128),
            (0, 128, 128, 128),
        ),
        buttons=(
            Button(label="Back", action=back_to_main),
        ),
        sliders=(
            Slider(
                label="Master Volume",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                default=DEFAULT_MASTER_VOLUME,
                action=apply_master_volume,
            ),
            Slider(
                label="Music Volume",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                default=DEFAULT_MUSIC_VOLUME,
                action=apply_music_volume,
            ),
            Slider(
                label="SFX Volume",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                default=DEFAULT_SFX_VOLUME,
                action=apply_sfx_volume,
            ),
        ),
    ),
}
