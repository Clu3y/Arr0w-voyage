"""与图形界面无关的棋盘路径判断逻辑。"""

from __future__ import annotations

from typing import Optional, TypeAlias


Cell: TypeAlias = Optional[str]
Board: TypeAlias = list[list[Cell]]

DIRECTIONS: dict[str, tuple[int, int]] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}


def can_fly_out(board: Board, row: int, col: int) -> bool:
    """判断指定位置的箭头前方是否存在其他箭头。"""
    if not board or not board[0]:
        raise ValueError("棋盘不能为空")
    if not (0 <= row < len(board) and 0 <= col < len(board[0])):
        raise IndexError("箭头坐标超出棋盘范围")

    direction = board[row][col]
    if direction not in DIRECTIONS:
        raise ValueError(f"未知箭头方向: {direction!r}")

    delta_row, delta_col = DIRECTIONS[direction]
    row += delta_row
    col += delta_col

    while 0 <= row < len(board) and 0 <= col < len(board[0]):
        if board[row][col] is not None:
            return False
        row += delta_row
        col += delta_col

    return True


def count_remaining_arrows(board: Board) -> int:
    """统计棋盘上尚未消除的箭头数量。"""
    return sum(cell is not None for row in board for cell in row)
