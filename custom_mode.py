"""自定义模式配置界面、长条滑块与随机棋盘生成。"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from logic import DIRECTIONS, Board, can_fly_out
from tools import ToolId
from ui import (
    ACCENT,
    INK,
    INK_SOFT,
    MOSS,
    PAPER_DEEP,
    PAPER_HOVER,
    PAPER_LIGHT,
    Button,
    load_font,
)


MIN_BOARD_SIZE = 1
MAX_BOARD_SIZE = 10
MIN_TOOL_COUNT = 0
MAX_TOOL_COUNT = 9
DEFAULT_DIFFICULTY = 0.30
DIAL_FACE = (245, 236, 218)
DIAL_BORDER = (207, 190, 163)


@dataclass(frozen=True)
class CustomModeConfig:
    """一局自定义游戏的完整配置。"""

    board_size: int = 5
    hint_count: int = 1
    extra_mistake_count: int = 1
    remove_count: int = 1
    difficulty: float = DEFAULT_DIFFICULTY

    def __post_init__(self) -> None:
        if not MIN_BOARD_SIZE <= self.board_size <= MAX_BOARD_SIZE:
            raise ValueError("棋盘大小必须在 1 到 10 之间")
        for count in (
            self.hint_count,
            self.extra_mistake_count,
            self.remove_count,
        ):
            if not MIN_TOOL_COUNT <= count <= MAX_TOOL_COUNT:
                raise ValueError("道具数量必须在 0 到 9 之间")
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError("难度系数必须在 0 到 1 之间")

    @property
    def empty_ratio(self) -> float:
        """返回难度系数直接控制的空位置比例。"""
        return self.difficulty

    def tool_counts(self) -> dict[ToolId, int]:
        """转换为道具状态模块使用的计数字典。"""
        return {
            ToolId.HINT: self.hint_count,
            ToolId.EXTRA_MISTAKE: self.extra_mistake_count,
            ToolId.REMOVE: self.remove_count,
        }


def generate_random_board(
    board_size: int,
    difficulty: float,
    *,
    rng: random.Random | None = None,
) -> Board:
    """生成保证可解、且空位置比例接近难度的随机棋盘。

    生成采用“反向放置”法：每次放置的箭头在放置当时都可以直接飞出。
    随后按放置顺序的逆序操作，必定可以清空棋盘。
    """

    if not MIN_BOARD_SIZE <= board_size <= MAX_BOARD_SIZE:
        raise ValueError("棋盘大小必须在 1 到 10 之间")
    if not 0.0 <= difficulty <= 1.0:
        raise ValueError("难度系数必须在 0 到 1 之间")

    generator = rng or random.Random()
    total_cells = board_size * board_size
    empty_count = min(total_cells - 1, round(total_cells * difficulty))
    arrow_count = total_cells - empty_count

    positions = [
        (row, col)
        for row in range(board_size)
        for col in range(board_size)
    ]
    selected = generator.sample(positions, arrow_count)
    # 越靠近中心的箭头越先放置，这样它到最近边缘的路径仍为空。
    selected.sort(
        key=lambda cell: min(
            cell[0],
            cell[1],
            board_size - 1 - cell[0],
            board_size - 1 - cell[1],
        ),
        reverse=True,
    )

    board: Board = [[None for _ in range(board_size)] for _ in range(board_size)]
    for row, col in selected:
        clear_directions: list[str] = []
        for direction in DIRECTIONS:
            board[row][col] = direction
            if can_fly_out(board, row, col):
                clear_directions.append(direction)
            board[row][col] = None
        if not clear_directions:
            continue
        board[row][col] = generator.choice(clear_directions)

    return board


def create_random_board(
    board_size: int,
    difficulty: float,
    *,
    rng: random.Random | None = None,
) -> Board:
    """兼容不同调用习惯的随机棋盘工厂。"""
    return generate_random_board(board_size, difficulty, rng=rng)


class BarSlider:
    """用横向长条和圆形手柄调节一个有限区间的数值。"""

    def __init__(
        self,
        key: str,
        label: str,
        rect: pygame.Rect,
        minimum: float,
        maximum: float,
        step: float,
        value: float,
        *,
        value_formatter=None,
    ) -> None:
        self.key = key
        self.label = label
        self.rect = rect
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.value_formatter = value_formatter or (lambda value: str(value))
        self.active = False
        self._value = float(value)
        self.set_value(value)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self.set_value(value)

    def set_value(self, value: float) -> None:
        clamped = min(self.maximum, max(self.minimum, float(value)))
        steps = round((clamped - self.minimum) / self.step)
        snapped = self.minimum + steps * self.step
        self._value = round(
            min(self.maximum, max(self.minimum, snapped)),
            10,
        )

    def display_value(self) -> str:
        return self.value_formatter(self.value)

    def contains(self, position: tuple[int, int]) -> bool:
        hit_rect = pygame.Rect(
            self.rect.left,
            self.rect.centery - 24,
            self.rect.width,
            48,
        )
        return hit_rect.collidepoint(position)

    def _ratio(self) -> float:
        if self.maximum == self.minimum:
            return 0.0
        return (self.value - self.minimum) / (self.maximum - self.minimum)

    def knob_position(self) -> tuple[int, int]:
        knob_x = round(self.rect.left + self.rect.width * self._ratio())
        return knob_x, self.rect.centery

    def set_from_position(self, position: tuple[int, int]) -> None:
        ratio = (position[0] - self.rect.left) / self.rect.width
        ratio = min(1.0, max(0.0, ratio))
        self.set_value(self.minimum + ratio * (self.maximum - self.minimum))

    def draw(
        self,
        surface: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
        hint_font: pygame.font.Font,
    ) -> None:
        center_y = self.rect.centery
        track_rect = pygame.Rect(
            self.rect.left,
            center_y - 6,
            self.rect.width,
            12,
        )

        label = label_font.render(self.label, True, INK)
        label_rect = label.get_rect(
            midright=(self.rect.left - 26, center_y)
        )
        surface.blit(label, label_rect)

        value_text = self.display_value()
        value = value_font.render(value_text, True, INK)
        value_rect = value.get_rect(
            midleft=(self.rect.right + 26, center_y)
        )
        value_background = value_rect.inflate(18, 10)
        pygame.draw.rect(
            surface,
            DIAL_FACE,
            value_background,
            border_radius=9,
        )
        pygame.draw.rect(
            surface,
            DIAL_BORDER,
            value_background,
            width=1,
            border_radius=9,
        )
        surface.blit(value, value_rect)

        pygame.draw.rect(
            surface,
            PAPER_DEEP,
            track_rect,
            border_radius=6,
        )

        step_count = round((self.maximum - self.minimum) / self.step)
        if step_count <= 10:
            for index in range(1, step_count):
                tick_x = round(
                    track_rect.left + track_rect.width * index / step_count
                )
                pygame.draw.line(
                    surface,
                    PAPER_LIGHT,
                    (tick_x, track_rect.top + 2),
                    (tick_x, track_rect.bottom - 2),
                    1,
                )

        progress_rect = pygame.Rect(
            track_rect.left,
            track_rect.top,
            round(track_rect.width * self._ratio()),
            track_rect.height,
        )
        if progress_rect.width > 0:
            pygame.draw.rect(
                surface,
                MOSS,
                progress_rect,
                border_radius=6,
            )

        knob_x, knob_y = self.knob_position()
        pygame.draw.circle(surface, PAPER_LIGHT, (knob_x, knob_y), 11)
        pygame.draw.circle(surface, ACCENT, (knob_x, knob_y), 11, width=3)
        pygame.draw.circle(surface, ACCENT, (knob_x, knob_y), 4)

        minimum = hint_font.render(
            self.value_formatter(self.minimum),
            True,
            INK_SOFT,
        )
        maximum = hint_font.render(
            self.value_formatter(self.maximum),
            True,
            INK_SOFT,
        )
        minimum_rect = minimum.get_rect(
            center=(track_rect.left, track_rect.bottom + 13)
        )
        maximum_rect = maximum.get_rect(
            center=(track_rect.right, track_rect.bottom + 13)
        )
        surface.blit(minimum, minimum_rect)
        surface.blit(maximum, maximum_rect)


class CustomModeConfigScreen:
    """游戏开始界面前的完整自定义配置页面。"""

    def __init__(self, background: pygame.Surface) -> None:
        self.background = background
        self.title_font = load_font(46, bold=True)
        self.subtitle_font = load_font(20)
        self.label_font = load_font(18, bold=True)
        self.value_font = load_font(20, bold=True)
        self.hint_font = load_font(12)
        self.explanation_font = load_font(17)
        self.button_font = load_font(23, bold=True)

        row_centers = (160, 225, 290, 355, 420)
        slider_rects = [
            pygame.Rect(280, center_y - 20, 420, 40)
            for center_y in row_centers
        ]
        self.sliders = {
            "board_size": BarSlider(
                "board_size",
                "棋盘大小",
                slider_rects[0],
                1,
                10,
                1,
                5,
                value_formatter=lambda value: f"{int(value)}×{int(value)}",
            ),
            "hint_count": BarSlider(
                "hint_count",
                "提示数量",
                slider_rects[1],
                0,
                9,
                1,
                1,
                value_formatter=lambda value: f"X{int(value)}",
            ),
            "extra_mistake_count": BarSlider(
                "extra_mistake_count",
                "增加失误次数",
                slider_rects[2],
                0,
                9,
                1,
                1,
                value_formatter=lambda value: f"X{int(value)}",
            ),
            "remove_count": BarSlider(
                "remove_count",
                "移出数量",
                slider_rects[3],
                0,
                9,
                1,
                1,
                value_formatter=lambda value: f"X{int(value)}",
            ),
            "difficulty": BarSlider(
                "difficulty",
                "难度系数",
                slider_rects[4],
                0.0,
                1.0,
                0.05,
                DEFAULT_DIFFICULTY,
                value_formatter=lambda value: f"{round(value * 100)}%",
            ),
        }
        self.start_button = Button(
            pygame.Rect(310, 508, 160, 56),
            "开始游戏",
            radius=12,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=DIAL_BORDER,
            border_width=1,
        )
        self.back_button = Button(
            pygame.Rect(490, 508, 160, 56),
            "返回",
            radius=12,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=DIAL_BORDER,
            border_width=1,
        )
        self.reset()

    def reset(self) -> None:
        defaults = {
            "board_size": 5,
            "hint_count": 1,
            "extra_mistake_count": 1,
            "remove_count": 1,
            "difficulty": DEFAULT_DIFFICULTY,
        }
        for key, value in defaults.items():
            self.sliders[key].set_value(value)
            self.sliders[key].active = False

    @property
    def config(self) -> CustomModeConfig:
        return CustomModeConfig(
            board_size=round(self.sliders["board_size"].value),
            hint_count=round(self.sliders["hint_count"].value),
            extra_mistake_count=round(
                self.sliders["extra_mistake_count"].value
            ),
            remove_count=round(self.sliders["remove_count"].value),
            difficulty=self.sliders["difficulty"].value,
        )

    def set_value(self, key: str, value: float) -> None:
        if key not in self.sliders:
            raise KeyError(key)
        self.sliders[key].set_value(value)

    def get_value(self, key: str) -> float:
        if key not in self.sliders:
            raise KeyError(key)
        return self.sliders[key].value

    def hover_target_at(self, position: tuple[int, int]) -> str | None:
        for key, slider in self.sliders.items():
            if slider.contains(position):
                return f"slider:{key}"
        if self.start_button.contains(position):
            return "custom_start"
        if self.back_button.contains(position):
            return "custom_back"
        return None

    def handle_mouse_down(self, position: tuple[int, int]) -> str | None:
        for key, slider in self.sliders.items():
            if slider.contains(position):
                slider.active = True
                slider.set_from_position(position)
                return f"slider:{key}"
        if self.start_button.contains(position):
            return "start"
        if self.back_button.contains(position):
            return "back"
        return None

    def handle_mouse_motion(self, position: tuple[int, int]) -> bool:
        for slider in self.sliders.values():
            if slider.active:
                slider.set_from_position(position)
                return True
        return False

    def handle_mouse_up(self) -> None:
        for slider in self.sliders.values():
            slider.active = False

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))
        pygame.draw.line(surface, ACCENT, (84, 76), (84, 590), 3)
        pygame.draw.circle(surface, ACCENT, (84, 76), 5)

        title = self.title_font.render("自定义模式", True, INK)
        title_rect = title.get_rect(center=(480, 55))
        surface.blit(title, title_rect)

        subtitle = self.subtitle_font.render(
            "拖动长条设置棋盘、道具次数与空位置比例",
            True,
            INK_SOFT,
        )
        subtitle_rect = subtitle.get_rect(center=(480, 100))
        surface.blit(subtitle, subtitle_rect)

        for index, slider in enumerate(self.sliders.values()):
            row_rect = pygame.Rect(
                92,
                slider.rect.centery - 26,
                776,
                52,
            )
            fill = PAPER_LIGHT if index % 2 == 0 else (238, 228, 208)
            pygame.draw.rect(surface, fill, row_rect, border_radius=10)
            pygame.draw.rect(
                surface,
                DIAL_BORDER,
                row_rect,
                width=1,
                border_radius=10,
            )
            slider.draw(
                surface,
                self.label_font,
                self.value_font,
                self.hint_font,
            )

        note = self.explanation_font.render(
            "难度系数越高，空位置比例越大；棋盘始终至少保留 1 支箭头。",
            True,
            INK_SOFT,
        )
        note_rect = note.get_rect(center=(480, 477))
        surface.blit(note, note_rect)

        mouse_position = pygame.mouse.get_pos()
        self.start_button.draw(surface, self.button_font, mouse_position)
        self.back_button.draw(surface, self.button_font, mouse_position)
