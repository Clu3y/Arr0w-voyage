"""自定义模式配置、随机棋盘与流程测试。"""

import os
import random

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from custom_mode import CustomModeConfig, generate_random_board
from game import Game, GameState
from logic import DIRECTIONS, Board, can_fly_out, count_remaining_arrows
from tools import ToolId, ToolState


def next_flyable_arrow(board: Board) -> tuple[int, int]:
    """返回当前可直接飞出的箭头坐标。"""
    target = next(
        (
            (row, col)
            for row, cells in enumerate(board)
            for col, direction in enumerate(cells)
            if direction is not None and can_fly_out(board, row, col)
        ),
        None,
    )
    assert target is not None
    return target


def solve_board(board: Board) -> None:
    """按可飞出箭头顺序清空棋盘，无法继续时立即失败。"""
    while count_remaining_arrows(board) > 0:
        row, col = next_flyable_arrow(board)
        board[row][col] = None


def solve_custom_game(game: Game) -> None:
    """通过真实点击流程清空自定义棋盘并等待结算状态。"""
    while count_remaining_arrows(game.board) > 0:
        game._click_arrow(*next_flyable_arrow(game.board))
    game.update(1.0)


@pytest.fixture
def game() -> Game:
    instance = Game()
    yield instance
    pygame.quit()


def test_custom_config_validation_and_defaults() -> None:
    config = CustomModeConfig()

    assert config.board_size == 5
    assert config.hint_count == 1
    assert config.extra_mistake_count == 1
    assert config.remove_count == 1
    assert 0.0 <= config.difficulty <= 1.0

    with pytest.raises(ValueError):
        CustomModeConfig(board_size=0)
    with pytest.raises(ValueError):
        CustomModeConfig(hint_count=10)
    with pytest.raises(ValueError):
        CustomModeConfig(difficulty=1.1)


@pytest.mark.parametrize("board_size", (1, 2, 5, 10))
@pytest.mark.parametrize("difficulty", (0.0, 0.3, 1.0))
def test_random_board_shape_empty_ratio_and_solvability(
    board_size: int,
    difficulty: float,
) -> None:
    board = generate_random_board(
        board_size,
        difficulty,
        rng=random.Random(20260915 + board_size),
    )

    assert len(board) == board_size
    assert all(len(row) == board_size for row in board)
    arrows = count_remaining_arrows(board)
    expected_arrows = board_size * board_size - min(
        board_size * board_size - 1,
        round(board_size * board_size * difficulty),
    )
    assert arrows == expected_arrows
    assert all(
        direction is None or direction in DIRECTIONS
        for row in board
        for direction in row
    )
    solve_board(board)


def test_custom_configuration_starts_with_selected_values(game: Game) -> None:
    game.return_to_start()
    game._handle_click(game.custom_mode_button.rect.center)
    assert game.state is GameState.CUSTOM_CONFIG

    screen = game.custom_mode_screen
    screen.set_value("board_size", 4)
    screen.set_value("hint_count", 3)
    screen.set_value("extra_mistake_count", 2)
    screen.set_value("remove_count", 0)
    screen.set_value("difficulty", 0.25)
    game._handle_click(screen.start_button.rect.center)

    assert game.state is GameState.PLAYING
    assert game.is_custom_mode is True
    assert len(game.board) == 4
    assert all(len(row) == 4 for row in game.board)
    assert game.tools.remaining[ToolId.HINT] == 3
    assert game.tools.remaining[ToolId.EXTRA_MISTAKE] == 2
    assert game.tools.remaining[ToolId.REMOVE] == 0
    assert game.max_mistakes == 3
    assert game.mistakes == 0


def test_custom_success_uses_replay_button_and_regenerates(game: Game) -> None:
    game.return_to_start()
    game._handle_click(game.custom_mode_button.rect.center)
    game.custom_mode_screen.set_value("board_size", 4)
    game.custom_mode_screen.set_value("difficulty", 0.3)
    game._handle_click(game.custom_mode_screen.start_button.rect.center)

    solve_custom_game(game)

    assert game.state is GameState.CUSTOM_COMPLETE
    game.draw()
    assert game.result_primary_button.text == "再来一局"

    game._handle_click(game.result_primary_button.rect.center)
    assert game.state is GameState.PLAYING
    assert game.is_custom_mode is True
    assert len(game.board) == 4
    assert game.mistakes == 0


def test_bar_slider_drag_maps_to_minimum_and_maximum(game: Game) -> None:
    game.return_to_start()
    game._handle_click(game.custom_mode_button.rect.center)
    slider = game.custom_mode_screen.sliders["board_size"]

    slider.set_from_position((slider.rect.left, slider.rect.centery))
    assert slider.value == 1

    slider.set_from_position((slider.rect.right, slider.rect.centery))
    assert slider.value == 10


def test_escape_returns_from_custom_config_to_start(game: Game) -> None:
    game.return_to_start()
    game._handle_click(game.custom_mode_button.rect.center)
    assert game.state is GameState.CUSTOM_CONFIG

    game._handle_keydown(pygame.K_ESCAPE)

    assert game.state is GameState.START


def test_tool_state_supports_multiple_uses() -> None:
    state = ToolState()
    state.reset(
        {
            ToolId.HINT: 2,
            ToolId.EXTRA_MISTAKE: 0,
            ToolId.REMOVE: 1,
        }
    )

    assert state.consume(ToolId.HINT) is True
    assert state.remaining[ToolId.HINT] == 1
    assert state.consume(ToolId.HINT) is True
    assert state.consume(ToolId.HINT) is False
    assert state.is_used(ToolId.EXTRA_MISTAKE) is True
