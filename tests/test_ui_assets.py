"""UI 素材和棕色背景测试。"""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ui import (
    ARROW_ASSET_FILES,
    BUTTON_ASSET_FILE,
    CELL_ASSET_FILE,
    CURSOR_ASSET_FILE,
    DIALOG_BUTTON_ASSET,
    DIALOG_CLOSE_ASSET,
    DIALOG_HEADER_ASSET,
    DIALOG_PANEL_ASSET,
    GAME_LOGO_FILE,
    GAME_SCREEN_BACKGROUND_ASSET,
    GITHUB_ICON_FILE,
    START_LOGO_FILE,
    TOOL_ASSET_FILES,
    TOOL_FRAME_ASSET,
    create_paper_background,
    get_nine_slice_background,
    get_nine_slice_ui_asset,
    load_background_asset,
    load_ui_asset,
)


def test_all_ui_assets_can_be_loaded() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    filenames = (
        *ARROW_ASSET_FILES.values(),
        *TOOL_ASSET_FILES.values(),
        BUTTON_ASSET_FILE,
        CELL_ASSET_FILE,
        CURSOR_ASSET_FILE,
        GITHUB_ICON_FILE,
        START_LOGO_FILE,
        GAME_LOGO_FILE,
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
        GAME_SCREEN_BACKGROUND_ASSET,
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


def test_game_background_expands_safe_area_without_changing_size() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    background = get_nine_slice_background(
        GAME_SCREEN_BACKGROUND_ASSET,
        (960, 640),
        (40, 20, 40, 20),
    )

    assert background is not None
    assert background.get_size() == (960, 640)
    pygame.quit()

def test_button_asset_uses_nine_slice_scaling() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    button = get_nine_slice_ui_asset(
        BUTTON_ASSET_FILE,
        (210, 52),
        (12, 9, 12, 9),
    )
    hover = get_nine_slice_ui_asset(
        BUTTON_ASSET_FILE,
        (210, 52),
        (12, 9, 12, 9),
        tint=(174, 58, 43),
    )

    assert button is not None
    assert hover is not None
    assert button.get_size() == (210, 52)
    assert hover.get_size() == (210, 52)
    assert button.get_at((105, 26)).a > 0
    assert button.get_at((0, 0)).a == 0
    assert button.get_at((105, 26)) != hover.get_at((105, 26))

    pygame.quit()
