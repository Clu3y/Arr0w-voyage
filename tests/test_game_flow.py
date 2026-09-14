"""通关、失败、重试和关卡切换的流程测试。"""

import copy
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from game import Game, GameState
from levels import LEVELS
from logic import can_fly_out, count_remaining_arrows
from tools import ToolId


def solve_current_level(game: Game) -> None:
    """按任意可通关顺序清空当前关卡。"""
    while count_remaining_arrows(game.board) > 0:
        target = next(
            (row, col)
            for row, cells in enumerate(game.board)
            for col, direction in enumerate(cells)
            if direction is not None and can_fly_out(game.board, row, col)
        )
        game._click_arrow(*target)
    game.update(1.0)


def lose_current_level(game: Game) -> None:
    """连续点击一个被阻挡的箭头，直到失误次数耗尽。"""
    target = next(
        (row, col)
        for row, cells in enumerate(game.board)
        for col, direction in enumerate(cells)
        if direction is not None and not can_fly_out(game.board, row, col)
    )
    for _ in range(game.max_mistakes):
        game._click_arrow(*target)
    game.update(0.5)


@pytest.fixture
def game() -> Game:
    instance = Game()
    instance.start_game()
    yield instance
    pygame.quit()


def test_clearing_level_opens_complete_screen(game: Game) -> None:
    solve_current_level(game)

    assert game.state is GameState.LEVEL_COMPLETE
    assert game.round_finished is True
    assert count_remaining_arrows(game.board) == 0
    assert game.current_level_index == 0


def test_last_arrow_finishes_flying_before_result_screen(game: Game) -> None:
    while count_remaining_arrows(game.board) > 1:
        target = next(
            (row, col)
            for row, cells in enumerate(game.board)
            for col, direction in enumerate(cells)
            if direction is not None and can_fly_out(game.board, row, col)
        )
        game._click_arrow(*target)

    final_target = next(
        (row, col)
        for row, cells in enumerate(game.board)
        for col, direction in enumerate(cells)
        if direction is not None and can_fly_out(game.board, row, col)
    )
    game._click_arrow(*final_target)

    assert game.state is GameState.PLAYING
    assert game.pending_result is GameState.LEVEL_COMPLETE
    assert game.effects.has_flying_arrows is True

    game.update(0.5)
    assert game.state is GameState.LEVEL_COMPLETE
    assert game.pending_result is None


def test_flying_arrow_can_be_drawn_midflight(game: Game) -> None:
    target = next(
        (row, col)
        for row, cells in enumerate(game.board)
        for col, direction in enumerate(cells)
        if direction is not None and can_fly_out(game.board, row, col)
    )
    game._click_arrow(*target)
    game.update(0.18)

    assert game.effects.has_flying_arrows is True
    game.draw()
    assert pygame.display.get_surface() is not None


def test_next_level_button_preserves_consumed_tools(game: Game) -> None:
    assert game.tools.consume(ToolId.HINT) is True
    solve_current_level(game)
    game._handle_click(game.result_primary_button.rect.center)

    assert game.state is GameState.PLAYING
    assert game.current_level_index == 1
    assert game.board == copy.deepcopy(LEVELS[1])
    assert game.mistakes == 0
    assert game.round_finished is False
    assert game.tools.remaining[ToolId.HINT] == 0
    assert game.tools.remaining[ToolId.EXTRA_MISTAKE] == 1
    assert game.tools.remaining[ToolId.REMOVE] == 1


def test_next_level_preserves_remaining_mistakes(game: Game) -> None:
    blocked = next(
        (row, col)
        for row, cells in enumerate(game.board)
        for col, direction in enumerate(cells)
        if direction is not None and not can_fly_out(game.board, row, col)
    )
    game._click_arrow(*blocked)
    game.update(0.5)
    game._click_arrow(*blocked)
    game.update(0.5)
    assert game.mistakes == 2

    solve_current_level(game)
    game._handle_click(game.result_primary_button.rect.center)

    assert game.state is GameState.PLAYING
    assert game.current_level_index == 1
    assert game.mistakes == 2
    assert game.max_mistakes - game.mistakes == 1


def test_final_level_opens_game_complete_and_can_replay(game: Game) -> None:
    game.current_level_index = len(LEVELS) - 1
    game._load_level()
    game.tools.consume(ToolId.HINT)
    solve_current_level(game)

    assert game.state is GameState.GAME_COMPLETE

    game._handle_click(game.result_primary_button.rect.center)
    assert game.state is GameState.PLAYING
    assert game.current_level_index == 0
    assert game.board == copy.deepcopy(LEVELS[0])
    assert game.mistakes == 0
    assert all(remaining == 1 for remaining in game.tools.remaining.values())


def test_restart_returns_to_first_level_and_resets_tools(game: Game) -> None:
    game.current_level_index = 1
    game._load_level()
    game.tools.consume(ToolId.HINT)

    game.restart_level()

    assert game.state is GameState.PLAYING
    assert game.current_level_index == 0
    assert game.board == copy.deepcopy(LEVELS[0])
    assert game.mistakes == 0
    assert all(remaining == 1 for remaining in game.tools.remaining.values())


def test_mistakes_exhausted_opens_lose_screen_and_retries(game: Game) -> None:
    level_index = game.current_level_index
    initial_board = copy.deepcopy(game.board)

    lose_current_level(game)
    assert game.state is GameState.LOSE
    assert game.mistakes == game.max_mistakes
    assert game.round_finished is True

    game._handle_click(game.result_primary_button.rect.center)
    assert game.state is GameState.PLAYING
    assert game.current_level_index == level_index
    assert game.board == initial_board
    assert game.mistakes == 0
    assert game.round_finished is False


def test_last_collision_feedback_finishes_before_lose_screen(game: Game) -> None:
    target = next(
        (row, col)
        for row, cells in enumerate(game.board)
        for col, direction in enumerate(cells)
        if direction is not None and not can_fly_out(game.board, row, col)
    )
    for _ in range(game.max_mistakes - 1):
        game._click_arrow(*target)
        game.update(0.5)

    game._click_arrow(*target)
    assert game.state is GameState.PLAYING
    assert game.pending_result is GameState.LOSE
    assert game.effects.feedback_cell == target

    game.update(0.5)
    assert game.state is GameState.LOSE


def test_result_screen_can_return_to_start(game: Game) -> None:
    lose_current_level(game)

    game._handle_click(game.result_secondary_button.rect.center)
    assert game.state is GameState.START
    assert game.round_finished is False


def test_hover_click_sound_only_plays_when_entering_button(
    game: Game,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    played: list[str] = []
    monkeypatch.setattr(
        game.audio,
        "play",
        lambda name, volume=0.7: played.append(name),
    )
    game.return_to_start()

    game._update_hover_audio(game.start_button.rect.center)
    game._update_hover_audio(game.start_button.rect.center)
    assert played == ["click"]

    game._update_hover_audio((0, 0))
    game._update_hover_audio(game.start_button.rect.center)
    assert played == ["click", "click"]

    game._handle_click(game.start_button.rect.center)
    assert played == ["click", "click"]


def test_result_primary_button_matches_secondary_style(game: Game) -> None:
    primary = game.result_primary_button
    secondary = game.result_secondary_button

    assert primary.radius == secondary.radius
    assert primary.normal_fill == secondary.normal_fill
    assert primary.hover_fill == secondary.hover_fill
    assert primary.normal_text == secondary.normal_text
    assert primary.hover_text == secondary.hover_text
    assert primary.border_color == secondary.border_color
    assert primary.border_width == secondary.border_width


@pytest.mark.parametrize(
    "state",
    [GameState.LEVEL_COMPLETE, GameState.GAME_COMPLETE, GameState.LOSE],
)
def test_all_result_screens_draw(game: Game, state: GameState) -> None:
    game.state = state
    game.round_finished = True

    game.draw()

    assert pygame.display.get_surface() is not None
