"""界面动画和短时提示状态。"""

from __future__ import annotations

from dataclasses import dataclass, field


Position = tuple[int, int]


@dataclass
class FlyingArrow:
    """描述一支正在飞出棋盘的箭头。"""

    row: int
    col: int
    direction: str
    duration: float = 0.48
    elapsed: float = 0.0

    @property
    def progress(self) -> float:
        """返回带缓出效果的水平，范围 0 到 1。"""
        if self.duration <= 0:
            return 1.0
        linear = min(1.0, max(0.0, self.elapsed / self.duration))
        return 1.0 - (1.0 - linear) ** 3


@dataclass
class AnimationState:
    """统一管理飞出、碰撞、提示和顶部 Toast 的计时。"""

    flying_arrows: list[FlyingArrow] = field(default_factory=list)
    feedback_cell: Position | None = None
    feedback_timer: float = 0.0
    hint_cell: Position | None = None
    hint_timer: float = 0.0
    toast_text: str | None = None
    toast_timer: float = 0.0

    def reset(self) -> None:
        self.flying_arrows.clear()
        self.feedback_cell = None
        self.feedback_timer = 0.0
        self.hint_cell = None
        self.hint_timer = 0.0
        self.toast_text = None
        self.toast_timer = 0.0

    def show_feedback(self, cell: Position, duration: float = 0.45) -> None:
        self.feedback_cell = cell
        self.feedback_timer = duration

    def start_fly(
        self,
        cell: Position,
        direction: str,
        duration: float = 0.48,
    ) -> None:
        """记录一支箭头的飞出动画。"""
        self.flying_arrows.append(
            FlyingArrow(
                row=cell[0],
                col=cell[1],
                direction=direction,
                duration=max(0.01, duration),
            )
        )

    @property
    def has_flying_arrows(self) -> bool:
        return bool(self.flying_arrows)

    def show_hint(self, cell: Position, duration: float = 1.8) -> None:
        self.hint_cell = cell
        self.hint_timer = duration

    def show_toast(self, text: str, duration: float = 1.8) -> None:
        self.toast_text = text
        self.toast_timer = duration

    def clear_feedback(self) -> None:
        self.feedback_cell = None
        self.feedback_timer = 0.0

    def clear_hint(self) -> None:
        self.hint_cell = None
        self.hint_timer = 0.0

    def update(self, delta_time: float) -> None:
        for arrow in self.flying_arrows:
            arrow.elapsed += delta_time
        self.flying_arrows = [
            arrow
            for arrow in self.flying_arrows
            if arrow.elapsed < arrow.duration
        ]

        if self.feedback_timer > 0:
            self.feedback_timer = max(0.0, self.feedback_timer - delta_time)
            if self.feedback_timer == 0:
                self.feedback_cell = None

        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - delta_time)
            if self.hint_timer == 0:
                self.hint_cell = None

        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - delta_time)
            if self.toast_timer == 0:
                self.toast_text = None
