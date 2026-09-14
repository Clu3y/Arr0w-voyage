"""界面动画和短时提示状态。"""

from __future__ import annotations

from dataclasses import dataclass


Position = tuple[int, int]


@dataclass
class AnimationState:
    """统一管理碰撞、提示和顶部 Toast 的计时。"""

    feedback_cell: Position | None = None
    feedback_timer: float = 0.0
    hint_cell: Position | None = None
    hint_timer: float = 0.0
    toast_text: str | None = None
    toast_timer: float = 0.0

    def reset(self) -> None:
        self.feedback_cell = None
        self.feedback_timer = 0.0
        self.hint_cell = None
        self.hint_timer = 0.0
        self.toast_text = None
        self.toast_timer = 0.0

    def show_feedback(self, cell: Position, duration: float = 0.45) -> None:
        self.feedback_cell = cell
        self.feedback_timer = duration

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
