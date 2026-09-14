"""音频资源和音频管理器测试。"""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from audio import MUSIC_FILES, SOUND_FILES, AudioManager


@pytest.mark.parametrize("path", [*SOUND_FILES.values(), *MUSIC_FILES.values()])
def test_audio_asset_exists(path) -> None:
    assert path.is_file()


def test_all_sound_assets_can_be_loaded() -> None:
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    for path in SOUND_FILES.values():
        sound = pygame.mixer.Sound(str(path))
        assert sound.get_length() > 0

    pygame.mixer.music.load(str(MUSIC_FILES["bgm"]))


def test_disabled_audio_manager_is_safe() -> None:
    manager = AudioManager(enabled=False)

    manager.play("click")
    manager.play_music("bgm")
    manager.stop_music()

    assert manager.enabled is False


def test_audio_manager_starts_bgm_loop() -> None:
    manager = AudioManager()

    manager.play_music("bgm")

    assert manager.enabled is True
    assert pygame.mixer.music.get_busy() is True
    manager.stop_music()
