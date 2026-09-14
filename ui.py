"""可复用的纸张风格界面组件。"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

import pygame


PAPER = (230, 215, 190)
PAPER_LIGHT = (243, 233, 213)
PAPER_DEEP = (207, 188, 156)
PAPER_HOVER = (220, 202, 169)
INK = (39, 40, 36)
INK_SOFT = (99, 88, 70)
RULE = (188, 170, 139)
ACCENT = (174, 58, 43)
MOSS = (78, 99, 67)

UI_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "ui"
BACKGROUND_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "background"
ARROW_ASSET_FILES = {
    "UP": "arrowUp.png",
    "DOWN": "arrowDown.png",
    "LEFT": "arrowLeft.png",
    "RIGHT": "arrowRight.png",
}
TOOL_ASSET_FILES = {
    "hint": "道具1.png",
    "extra_mistake": "道具2.png",
    "remove": "道具3.png",
}
CELL_ASSET_FILE = "方格.png"
CURSOR_ASSET_FILE = "鼠标.png"
DIALOG_PANEL_ASSET = "提示框背景.png"
DIALOG_HEADER_ASSET = "提示框头部.png"
DIALOG_CLOSE_ASSET = "关闭按钮.png"
DIALOG_BUTTON_ASSET = "按钮.png"
TOOL_FRAME_ASSET = "道具框.png"

_IMAGE_CACHE: dict[str, pygame.Surface] = {}
_SCALED_IMAGE_CACHE: dict[tuple[str, tuple[int, int], tuple[int, int] | None], pygame.Surface] = {}
_BACKGROUND_IMAGE_CACHE: dict[str, pygame.Surface] = {}
_BACKGROUND_SCALED_CACHE: dict[tuple[str, tuple[int, int], int], pygame.Surface] = {}

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


def load_ui_asset(filename: str) -> pygame.Surface | None:
    """加载并缓存 assets/ui 中的图片。"""
    cached = _IMAGE_CACHE.get(filename)
    if cached is not None:
        return cached

    path = UI_ASSET_DIR / filename
    if not path.is_file():
        return None

    try:
        image = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
    except pygame.error:
        return None

    _IMAGE_CACHE[filename] = image
    return image


def _tint_asset(
    image: pygame.Surface,
    color: tuple[int, int, int],
) -> pygame.Surface:
    """用图片的透明通道为黑色线性素材重新着色。"""
    tinted = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    tinted.fill((*color, 0))
    tinted.blit(image, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)
    return tinted


def get_scaled_ui_asset(
    filename: str,
    size: tuple[int, int],
    *,
    color: tuple[int, int, int] | None = None,
) -> pygame.Surface | None:
    """按显示尺寸缩放 UI 图片，并缓存结果。"""
    width, height = max(1, size[0]), max(1, size[1])
    scaled_size = (width, height)
    cache_key = (filename, scaled_size, color)
    cached = _SCALED_IMAGE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    image = load_ui_asset(filename)
    if image is None:
        return None

    scaled = pygame.transform.smoothscale(image, scaled_size)
    if color is not None:
        scaled = _tint_asset(scaled, color)

    _SCALED_IMAGE_CACHE[cache_key] = scaled
    return scaled


def load_background_asset(filename: str) -> pygame.Surface | None:
    """加载并缓存 assets/background 中的素材。"""
    cached = _BACKGROUND_IMAGE_CACHE.get(filename)
    if cached is not None:
        return cached

    path = BACKGROUND_ASSET_DIR / filename
    if not path.is_file():
        return None

    try:
        image = pygame.image.load(str(path))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
    except pygame.error:
        return None

    _BACKGROUND_IMAGE_CACHE[filename] = image
    return image


def get_scaled_background_asset(
    filename: str,
    size: tuple[int, int],
    *,
    rotate: int = 0,
) -> pygame.Surface | None:
    """缩放背景素材，可在缩放前旋转。"""
    width, height = max(1, size[0]), max(1, size[1])
    scaled_size = (width, height)
    cache_key = (filename, scaled_size, rotate)
    cached = _BACKGROUND_SCALED_CACHE.get(cache_key)
    if cached is not None:
        return cached

    image = load_background_asset(filename)
    if image is None:
        return None

    if rotate:
        image = pygame.transform.rotate(image, rotate)
    scaled = pygame.transform.scale(image, scaled_size)
    _BACKGROUND_SCALED_CACHE[cache_key] = scaled
    return scaled


def set_custom_cursor() -> bool:
    """设置自定义鼠标，不支持时安全回退到系统鼠标。"""
    image = load_ui_asset(CURSOR_ASSET_FILE)
    if image is None:
        return False
    image = pygame.transform.smoothscale(image, (10, 11))
    try:
        pygame.mouse.set_cursor(pygame.cursors.Cursor((1, 1), image))
    except pygame.error:
        return False
    return True


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
    """生成带有轻微颗粒感的暖棕色纸张背景。"""
    surface = pygame.Surface(size)
    surface.fill(PAPER)

    rng = random.Random(20260913)
    width, height = size
    for _ in range(width * height // 300):
        x = rng.randrange(width)
        y = rng.randrange(height)
        tone = rng.choice(((233, 219, 196), (226, 210, 183), (237, 225, 202)))
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

    asset_name = ARROW_ASSET_FILES.get(direction)
    if asset_name is not None:
        image = get_scaled_ui_asset(
            asset_name,
            (size, size),
            color=color,
        )
        if image is not None:
            rect = image.get_rect(center=(center_x, center_y))
            surface.blit(image, rect)
            return

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

    asset_name = TOOL_ASSET_FILES.get(tool)
    if asset_name is not None:
        image = get_scaled_ui_asset(
            asset_name,
            (30, 30),
            color=color,
        )
        if image is not None:
            rect = image.get_rect(center=(center_x, center_y))
            surface.blit(image, rect)
            return

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


def draw_cell_texture(surface: pygame.Surface, rect: pygame.Rect) -> bool:
    """绘制方格素材，加载失败时保留现有底色。"""
    image = get_scaled_ui_asset(CELL_ASSET_FILE, rect.size)
    if image is None:
        return False
    surface.blit(image, rect.topleft)
    return True

def draw_heart(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int,
    color: tuple[int, int, int],
) -> None:
    """绘制一颗简洁的心形。"""
    center_x, center_y = center
    half_width = size * 0.36
    lobe_radius = size * 0.22
    lobe_center_y = center_y - size * 0.12

    pygame.draw.circle(
        surface,
        color,
        (round(center_x - size * 0.18), round(lobe_center_y)),
        round(lobe_radius),
    )
    pygame.draw.circle(
        surface,
        color,
        (round(center_x + size * 0.18), round(lobe_center_y)),
        round(lobe_radius),
    )
    pygame.draw.polygon(
        surface,
        color,
        (
            (round(center_x - half_width), round(center_y - size * 0.04)),
            (round(center_x + half_width), round(center_y - size * 0.04)),
            (center_x, round(center_y + size * 0.42)),
        ),
    )
