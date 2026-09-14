"""音乐与音效接入模块。

当前没有音频资源，因此默认不加载。后续只需把资源路径补入
SOUND_FILES，并在创建 AudioManager 时设置 enabled=True。
"""

from __future__ import annotations

from pathlib import Path

import pygame


SOUND_FILES = {
    "fly": Path("assets/audio/fly.wav"),
    "blocked": Path("assets/audio/blocked.wav"),
    "hint": Path("assets/audio/hint.wav"),
    "heal": Path("assets/audio/heal.wav"),
    "remove": Path("assets/audio/remove.wav"),
    "win": Path("assets/audio/win.wav"),
}


class AudioManager:
    """统一管理后续音乐和音效资源。"""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._mixer_ready = False

        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_ready = True
        except pygame.error:
            self.enabled = False

    def play(self, name: str) -> None:
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

        sound.play()
