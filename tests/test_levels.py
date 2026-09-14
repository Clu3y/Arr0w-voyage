"""关卡数据完整性测试。"""

import copy

from levels import LEVELS
from logic import can_fly_out, count_remaining_arrows


def is_solvable(board: list[list[str | None]]) -> bool:
    """检查关卡能否按当前可消除箭头逐层清空。"""
    return removal_waves(board) is not None


def removal_waves(board: list[list[str | None]]) -> list[int] | None:
    """按每轮同时移除全部可飞出箭头，返回各轮数量。"""
    next_board = copy.deepcopy(board)
    waves: list[int] = []
    while count_remaining_arrows(next_board) > 0:
        removable = [
            (row, col)
            for row, cells in enumerate(next_board)
            for col, direction in enumerate(cells)
            if direction is not None and can_fly_out(next_board, row, col)
        ]
        if not removable:
            return None
        waves.append(len(removable))
        for row, col in removable:
            next_board[row][col] = None

    return waves


def has_forbidden_symmetry(board: list[list[str | None]]) -> bool:
    """检查左右镜像、上下镜像和 180 度中心对称。"""
    horizontal = [row[::-1] for row in board]
    vertical = board[::-1]
    central = [row[::-1] for row in board[::-1]]
    return board in (horizontal, vertical, central)


def has_direct_mutual_block(board: list[list[str | None]]) -> bool:
    """检查是否存在两支箭头沿同一直线互相指向对方的死锁。"""
    vectors = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }
    rows = len(board)
    cols = len(board[0])

    for row in range(rows):
        for col in range(cols):
            direction = board[row][col]
            if direction is None:
                continue
            delta_row, delta_col = vectors[direction]
            other_row = row + delta_row
            other_col = col + delta_col

            while 0 <= other_row < rows and 0 <= other_col < cols:
                other_direction = board[other_row][other_col]
                if other_direction is not None:
                    back_row, back_col = vectors[other_direction]
                    if (other_row + back_row, other_col + back_col) == (row, col):
                        return True
                    break
                other_row += delta_row
                other_col += delta_col

    return False


def test_three_levels_are_defined() -> None:
    assert len(LEVELS) == 3


def test_level_difficulty_requirements() -> None:
    first, second, third = LEVELS

    assert (len(first), len(first[0])) == (5, 5)
    assert count_remaining_arrows(first) == 8

    assert (len(second), len(second[0])) == (5, 5)
    assert count_remaining_arrows(second) == 20
    assert count_remaining_arrows(second) / 25 == 0.8

    assert (len(third), len(third[0])) == (6, 6)
    assert count_remaining_arrows(third) == 36
    assert all(cell is not None for row in third for cell in row)


def test_advanced_levels_use_irregular_three_layer_dependencies() -> None:
    for board in LEVELS[1:]:
        total = count_remaining_arrows(board)
        waves = removal_waves(board)

        assert waves is not None
        assert 2 <= len(waves) <= 3
        assert waves[0] < total
        assert waves[0] / total <= 0.4
        assert has_forbidden_symmetry(board) is False
        assert has_direct_mutual_block(board) is False


def test_levels_are_rectangular() -> None:
    for board in LEVELS:
        assert board
        assert len({len(row) for row in board}) == 1


def test_all_levels_are_solvable() -> None:
    assert all(is_solvable(board) for board in LEVELS)
