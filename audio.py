"""背景音乐与音效管理。"""

from __future__ import annotations

from pathlib import Path

import pygame


ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "audio"

SOUND_FILES = {
    "click": ASSET_ROOT / "click.ogg",
    "fly": ASSET_ROOT / "fly.ogg",
    "miss": ASSET_ROOT / "miss.ogg",
    "win": ASSET_ROOT / "win.ogg",
    "fail": ASSET_ROOT / "fail.ogg",
}

MUSIC_FILES = {
    "bgm": ASSET_ROOT / "bgm.ogg",
}


class AudioManager:
    """统一管理背景音乐和短音效资源。"""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._mixer_ready = False
        self._music_name: str | None = None

        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(24)
            self._mixer_ready = True
        except pygame.error:
            self.enabled = False

    def play(self, name: str, volume: float = 0.7) -> None:
        """播放一次短音效。"""
        if not self.enabled or not self._mixer_ready:
            return

        sound = self._sounds.get(name)
        if sound is None:
            path = SOUND_FILES.get(name)
            if path is None or not path.is_file():
                return
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error:
                return
            self._sounds[name] = sound

        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()

    def play_music(
        self,
        name: str,
        *,
        volume: float = 0.38,
        fade_ms: int = 600,
    ) -> None:
        """循环播放背景音乐。"""
        if not self.enabled or not self._mixer_ready:
            return

        if self._music_name == name and pygame.mixer.music.get_busy():
            return

        path = MUSIC_FILES.get(name)
        if path is None or not path.is_file():
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            pygame.mixer.music.play(-1, fade_ms=fade_ms)
            self._music_name = name
        except pygame.error:
            return

    def stop_music(self, fade_ms: int = 400) -> None:
        if not self.enabled or not self._mixer_ready:
            return
        pygame.mixer.music.fadeout(max(0, fade_ms))
        self._music_name = None
