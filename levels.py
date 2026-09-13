"""关卡数据。

布局通过反向放置生成：每次放置时箭头到边界均无阻挡，
因此按放置顺序的逆序操作一定可以清空棋盘。
"""

from logic import Board


DIRECTION_SYMBOLS = {
    "↑": "UP",
    "↓": "DOWN",
    "←": "LEFT",
    "→": "RIGHT",
}


def _parse_level(rows: tuple[str, ...]) -> Board:
    """把可读的字符布局转换为棋盘二维数组。"""
    return [
        [DIRECTION_SYMBOLS.get(symbol) for symbol in row]
        for row in rows
    ]


LEVEL_NAMES = ("初试锋芒", "层层相扣", "最后一箭")

LEVELS: tuple[Board, ...] = (
    _parse_level(
        (
            "....↑",
            ".↑...",
            "↑...↓",
            ".↑.↓.",
            "←.↑..",
        )
    ),
    _parse_level(
        (
            "←.←..",
            "...←→",
            ".←.→.",
            ".↓.↑.",
            "↓...→",
        )
    ),
    _parse_level(
        (
            ".↑.↓.",
            "↑...↑",
            "←.↓.↓",
            ".←..→",
            "↓→.→.",
        )
    ),
)
