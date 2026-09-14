"""可复用的纸张风格界面组件。"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

import pygame


PAPER = (255, 255, 255)
PAPER_LIGHT = (246, 241, 228)
PAPER_DEEP = (225, 216, 193)
PAPER_HOVER = (232, 222, 198)
INK = (39, 40, 36)
INK_SOFT = (101, 97, 85)
RULE = (190, 180, 154)
ACCENT = (174, 58, 43)
MOSS = (78, 99, 67)

DIRECTION_VECTORS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """优先加载支持中文的字体，找不到时回退到默认字体。"""
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    font_names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf") if bold else (
        "msyh.ttc",
        "simhei.ttf",
        "msyhbd.ttc",
    )
    for font_name in font_names:
        font_path = windows / "Fonts" / font_name
        if font_path.is_file():
            try:
                return pygame.font.Font(str(font_path), size)
            except OSError:
                continue
    return pygame.font.Font(None, size)


class Button:
    """支持不同圆角与悬停配色的按钮。"""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        *,
        radius: int = 2,
        normal_fill: tuple[int, int, int] = PAPER_LIGHT,
        hover_fill: tuple[int, int, int] = INK,
        normal_text: tuple[int, int, int] = INK,
        hover_text: tuple[int, int, int] = PAPER_LIGHT,
        border_color: tuple[int, int, int] = INK,
        border_width: int = 2,
    ) -> None:
        self.rect = rect
        self.text = text
        self.radius = radius
        self.normal_fill = normal_fill
        self.hover_fill = hover_fill
        self.normal_text = normal_text
        self.hover_text = hover_text
        self.border_color = border_color
        self.border_width = border_width

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        mouse_position: tuple[int, int],
    ) -> None:
        hovered = self.contains(mouse_position)
        pygame.draw.rect(
            surface,
            self.hover_fill if hovered else self.normal_fill,
            self.rect,
            border_radius=self.radius,
        )
        pygame.draw.rect(
            surface,
            self.border_color,
            self.rect,
            width=self.border_width,
            border_radius=self.radius,
        )

        label = font.render(
            self.text,
            True,
            self.hover_text if hovered else self.normal_text,
        )
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


def create_paper_background(size: tuple[int, int]) -> pygame.Surface:
    """生成带有轻微纸张颗粒感的背景。"""
    surface = pygame.Surface(size)
    surface.fill(PAPER)

    rng = random.Random(20260913)
    width, height = size
    for _ in range(width * height // 300):
        x = rng.randrange(width)
        y = rng.randrange(height)
        tone = rng.choice(((250, 250, 249), (255, 255, 255), (247, 247, 246)))
        surface.set_at((x, y), tone)

    return surface


def draw_arrow(
    surface: pygame.Surface,
    center: tuple[int, int],
    direction: str,
    size: int,
    color: tuple[int, int, int] = INK,
    offset: int = 0,
) -> None:
    """按方向绘制一个由线杆和三角箭头组成的图形。"""
    vector_x, vector_y = DIRECTION_VECTORS[direction]
    center_x = center[0] + vector_x * offset
    center_y = center[1] + vector_y * offset

    length = size * 0.50
    head_length = size * 0.20
    head_width = size * 0.20
    shaft_width = max(3, int(size * 0.085))

    tip = (
        int(center_x + vector_x * length / 2),
        int(center_y + vector_y * length / 2),
    )
    tail = (
        int(center_x - vector_x * length / 2),
        int(center_y - vector_y * length / 2),
    )
    stem_end = (
        int(tip[0] - vector_x * head_length),
        int(tip[1] - vector_y * head_length),
    )
    perpendicular = (-vector_y, vector_x)
    head_base_left = (
        int(stem_end[0] + perpendicular[0] * head_width / 2),
        int(stem_end[1] + perpendicular[1] * head_width / 2),
    )
    head_base_right = (
        int(stem_end[0] - perpendicular[0] * head_width / 2),
        int(stem_end[1] - perpendicular[1] * head_width / 2),
    )

    pygame.draw.line(surface, color, tail, stem_end, shaft_width)
    pygame.draw.polygon(
        surface, color, (tip, head_base_left, head_base_right)
    )

def draw_tool_icon(
    surface: pygame.Surface,
    tool: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    """绘制提示、增加失误次数和移出道具的线性图标。"""
    center_x, center_y = center

    if tool == "hint":
        pygame.draw.circle(surface, color, (center_x, center_y - 3), 8, 2)
        pygame.draw.line(
            surface,
            color,
            (center_x - 4, center_y + 7),
            (center_x + 4, center_y + 7),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (center_x - 3, center_y + 11),
            (center_x + 3, center_y + 11),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (center_x, center_y - 17),
            (center_x, center_y - 13),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (center_x - 14, center_y - 4),
            (center_x - 10, center_y - 4),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (center_x + 10, center_y - 4),
            (center_x + 14, center_y - 4),
            2,
        )
        return

    if tool == "extra_mistake":
        pygame.draw.circle(surface, color, (center_x, center_y), 12, 2)
        pygame.draw.line(
            surface,
            color,
            (center_x, center_y - 6),
            (center_x, center_y + 6),
            2,
        )
        pygame.draw.line(
            surface,
            color,
            (center_x - 6, center_y),
            (center_x + 6, center_y),
            2,
        )
        return
    box = pygame.Rect(center_x - 12, center_y - 8, 17, 17)
    pygame.draw.rect(surface, color, box, width=2, border_radius=3)
    pygame.draw.line(
        surface,
        color,
        (center_x - 4, center_y + 3),
        (center_x + 10, center_y - 11),
        2,
    )
    pygame.draw.polygon(
        surface,
        color,
        (
            (center_x + 12, center_y - 13),
            (center_x + 5, center_y - 11),
            (center_x + 10, center_y - 6),
        ),
    )
