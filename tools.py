"""道具定义与可配置使用次数状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class ToolId(str, Enum):
    """游戏中的道具标识。"""

    HINT = "hint"
    EXTRA_MISTAKE = "extra_mistake"
    REMOVE = "remove"


TOOL_KEYS: tuple[ToolId, ...] = (
    ToolId.HINT,
    ToolId.EXTRA_MISTAKE,
    ToolId.REMOVE,
)

TOOL_LABELS = {
    ToolId.HINT: "提示",
    ToolId.EXTRA_MISTAKE: "增加失误次数",
    ToolId.REMOVE: "移出",
}

TOOL_DESCRIPTIONS = {
    ToolId.HINT: "高亮可走箭头",
    ToolId.EXTRA_MISTAKE: "恢复一颗红心",
    ToolId.REMOVE: "选择并移除箭头",
}


@dataclass
class ToolState:
    """维护每个道具的剩余次数和目标选择状态。"""

    remaining: dict[ToolId, int] = field(
        default_factory=lambda: {tool: 1 for tool in TOOL_KEYS}
    )
    pending: ToolId | None = None

    def reset(
        self,
        remaining: Mapping[ToolId, int] | None = None,
    ) -> None:
        """恢复到普通模式默认值，或使用指定次数。"""
        counts = {tool: 1 for tool in TOOL_KEYS}
        if remaining is not None:
            for tool in TOOL_KEYS:
                counts[tool] = max(0, int(remaining.get(tool, 1)))
        self.remaining = counts
        self.pending = None

    def is_used(self, tool: ToolId) -> bool:
        return self.remaining[tool] <= 0

    def consume(self, tool: ToolId) -> bool:
        if self.is_used(tool):
            return False
        self.remaining[tool] -= 1
        return True

    def begin_selection(self, tool: ToolId) -> None:
        self.pending = tool

    def cancel_selection(self) -> None:
        self.pending = None
