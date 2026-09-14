"""UI 素材和棕色背景测试。"""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ui import (
    ARROW_ASSET_FILES,
    CELL_ASSET_FILE,
    CURSOR_ASSET_FILE,
    DIALOG_BUTTON_ASSET,
    DIALOG_CLOSE_ASSET,
    DIALOG_HEADER_ASSET,
    DIALOG_PANEL_ASSET,
    TOOL_ASSET_FILES,
    TOOL_FRAME_ASSET,
    create_paper_background,
    load_background_asset,
    load_ui_asset,
)


def test_all_ui_assets_can_be_loaded() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    filenames = (
        *ARROW_ASSET_FILES.values(),
        *TOOL_ASSET_FILES.values(),
        CELL_ASSET_FILE,
        CURSOR_ASSET_FILE,
    )
    for filename in filenames:
        image = load_ui_asset(filename)
        assert image is not None
        assert image.get_width() > 0
        assert image.get_height() > 0

    pygame.quit()


def test_all_background_assets_can_be_loaded() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    filenames = (
        DIALOG_PANEL_ASSET,
        DIALOG_HEADER_ASSET,
        DIALOG_CLOSE_ASSET,
        DIALOG_BUTTON_ASSET,
        TOOL_FRAME_ASSET,
    )
    for filename in filenames:
        image = load_background_asset(filename)
        assert image is not None
        assert image.get_width() > 0
        assert image.get_height() > 0

    pygame.quit()


def test_paper_background_uses_warm_brown_tone() -> None:
    background = create_paper_background((8, 8))
    red, green, blue = background.get_at((0, 0))[:3]

    assert red > green > blue
