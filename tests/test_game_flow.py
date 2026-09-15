"""通关、失败、重试和关卡切换的流程测试。"""

import copy
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from game import Game, GameState, REPOSITORY_URL
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


def test_restart_button_requires_confirmation(game: Game) -> None:
    game.current_level_index = 1
    game._load_level()
    game.mistakes = 2
    game.tools.consume(ToolId.HINT)

    game._handle_click(game.restart_button.rect.center)
    assert game.dialog_action == "restart"
    assert game.current_level_index == 1

    game._handle_click(game.dialog_confirm_rect.center)
    assert game.dialog_action is None
    assert game.state is GameState.PLAYING
    assert game.current_level_index == 0
    assert game.mistakes == 0
    assert all(remaining == 1 for remaining in game.tools.remaining.values())


def test_exit_dialog_cancel_and_close_keep_game_running(game: Game) -> None:
    game._handle_click(game.exit_button.rect.center)
    assert game.dialog_action == "exit"

    game._handle_click(game.dialog_cancel_rect.center)
    assert game.dialog_action is None
    assert game.running is True

    game._handle_click(game.exit_button.rect.center)
    game._handle_click(game.dialog_close_rect.center)
    assert game.dialog_action is None
    assert game.running is True


def test_exit_dialog_confirmation_stops_game(game: Game) -> None:
    game._handle_click(game.exit_button.rect.center)
    game._handle_click(game.dialog_confirm_rect.center)

    assert game.dialog_action is None
    assert game.running is False


def test_dialog_blocks_underlying_game_clicks(game: Game) -> None:
    initial_level = game.current_level_index
    game._handle_click(game.restart_button.rect.center)

    game._handle_click(game.restart_button.rect.center)

    assert game.dialog_action == "restart"
    assert game.current_level_index == initial_level
    assert all(remaining == 1 for remaining in game.tools.remaining.values())


def test_dialog_header_overlap_and_close_button_position(game: Game) -> None:
    overlap = game.dialog_header_rect.bottom - game.dialog_panel_rect.top

    assert overlap == game.dialog_header_rect.height // 2
    assert game.dialog_panel_rect.contains(game.dialog_close_rect)


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


def test_author_link_opens_repository(
    game: Game,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[str] = []
    monkeypatch.setattr("game.webbrowser.open", opened.append)
    game.return_to_start()

    game._handle_click(game.author_link_rect.center)

    assert opened == [REPOSITORY_URL]


def test_author_link_is_hover_target(game: Game) -> None:
    game.return_to_start()

    assert game._hover_target_at(game.author_link_rect.center) == "author"


def test_start_and_result_controls_stay_inside_background_safe_area(
    game: Game,
) -> None:
    safe_area = pygame.Rect(40, 20, 880, 600)
    controls = (
        game.start_button.rect,
        game.custom_mode_button.rect,
        game.author_link_rect,
        game.restart_button.rect,
        game.exit_button.rect,
        game.result_primary_button.rect,
        game.result_secondary_button.rect,
        *game.tool_rects.values(),
    )

    assert all(safe_area.contains(rect) for rect in controls)


def test_custom_mode_button_opens_config_without_starting_game(game: Game) -> None:
    game.return_to_start()

    game._handle_click(game.custom_mode_button.rect.center)

    assert game.state is GameState.CUSTOM_CONFIG
    assert game.is_custom_mode is False


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
