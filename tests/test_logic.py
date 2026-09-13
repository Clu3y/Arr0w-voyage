"""路径检测逻辑的自动化测试。"""

import pytest

from logic import can_fly_out, count_remaining_arrows


def test_can_fly_out_when_path_is_clear() -> None:
    board = [[None, "RIGHT", None]]
    assert can_fly_out(board, 0, 1) is True


def test_blocked_by_another_arrow() -> None:
    board = [["RIGHT", "UP"]]
    assert can_fly_out(board, 0, 0) is False


@pytest.mark.parametrize(
    ("direction", "board", "row", "col"),
    [
        ("UP", [["UP"], [None]], 0, 0),
        ("DOWN", [[None], ["DOWN"]], 1, 0),
        ("LEFT", [[None, "LEFT"]], 0, 1),
        ("RIGHT", [["RIGHT", None]], 0, 0),
    ],
)
def test_arrow_on_edge_can_leave(
    direction: str, board: list[list[str | None]], row: int, col: int
) -> None:
    assert board[row][col] == direction
    assert can_fly_out(board, row, col) is True


def test_count_remaining_arrows_ignores_empty_cells() -> None:
    board = [["UP", None], [None, "LEFT"]]
    assert count_remaining_arrows(board) == 2


def test_invalid_coordinate_raises_index_error() -> None:
    with pytest.raises(IndexError):
        can_fly_out([["UP"]], 1, 0)
