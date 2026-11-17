"""Settings menu definition and volume controls for Raincloud games."""

from raincloud.scripts.userinterface import Button, Menu, Slider


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
    """Close the settings menu and return to the previous menu."""
    app.close_menu()


# Default volume values stored on the app so SFX can read them.
DEFAULT_MASTER_VOLUME = 1.0
DEFAULT_MUSIC_VOLUME = 1.0
DEFAULT_SFX_VOLUME = 1.0

# Trackbar width in pixels (matches MenuController.render).
SLIDER_TRACK_WIDTH = 200

MENUS = {
    "settings": Menu(
        title="Settings",
        matrix=(
            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0),
            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ),
        colors=(
            (15, 20, 32, 235),
            (22, 30, 45, 235),
            (31, 44, 62, 235),
            (48, 65, 84, 235),
            (76, 96, 114, 235),
            (111, 132, 148, 235),
            (157, 176, 190, 235),
            (213, 225, 233, 235),
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