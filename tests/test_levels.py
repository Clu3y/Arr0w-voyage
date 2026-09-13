"""关卡数据完整性测试。"""

import copy

from levels import LEVELS
from logic import can_fly_out, count_remaining_arrows


def is_solvable(board: list[list[str | None]]) -> bool:
    """回溯检查是否存在一条清空全部箭头的操作顺序。"""
    if count_remaining_arrows(board) == 0:
        return True

    for row, cells in enumerate(board):
        for col, direction in enumerate(cells):
            if direction is None or not can_fly_out(board, row, col):
                continue

            next_board = copy.deepcopy(board)
            next_board[row][col] = None
            if is_solvable(next_board):
                return True

    return False


def test_three_levels_are_defined() -> None:
    assert len(LEVELS) == 3


def test_levels_are_rectangular() -> None:
    for board in LEVELS:
        assert board
        assert len({len(row) for row in board}) == 1


def test_all_levels_are_solvable() -> None:
    assert all(is_solvable(board) for board in LEVELS)
