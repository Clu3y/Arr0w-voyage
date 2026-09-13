"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import math
import os
from enum import Enum, auto
from pathlib import Path

import pygame


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

BACKGROUND_TOP = (238, 245, 252)
BACKGROUND_BOTTOM = (215, 229, 242)
TITLE_COLOR = (25, 42, 66)
SUBTITLE_COLOR = (45, 111, 173)
TEXT_COLOR = (53, 70, 89)
MUTED_TEXT_COLOR = (102, 119, 138)
PANEL_COLOR = (248, 251, 254)
PANEL_BORDER_COLOR = (188, 210, 229)
BUTTON_COLOR = (35, 117, 184)
BUTTON_HOVER_COLOR = (25, 96, 157)
BUTTON_SHADOW_COLOR = (157, 184, 207)
BUTTON_TEXT_COLOR = (255, 255, 255)


class GameState(Enum):
    """游戏当前所处的大状态。"""

    START = auto()
    PLAYING = auto()


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """优先加载支持中文的字体，找不到时回退到 Pygame 默认字体。"""
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
    """带悬停效果的矩形按钮。"""

    def __init__(self, rect: pygame.Rect, text: str) -> None:
        self.rect = rect
        self.text = text

    def contains(self, position: tuple[int, int]) -> bool:
        """判断鼠标是否位于按钮范围内。"""
        return self.rect.collidepoint(position)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        mouse_position: tuple[int, int],
        elapsed_time: float,
    ) -> None:
        """绘制按钮及悬停动画。"""
        hovered = self.contains(mouse_position)
        float_offset = int(math.sin(elapsed_time * 3.0) * 2) if hovered else 0
        rect = self.rect.move(0, float_offset)
        shadow_rect = rect.move(0, 7)

        pygame.draw.rect(
            surface, BUTTON_SHADOW_COLOR, shadow_rect, border_radius=18
        )
        pygame.draw.rect(
            surface,
            BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR,
            rect,
            border_radius=18,
        )

        label = font.render(self.text, True, BUTTON_TEXT_COLOR)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)


class Game:
    """负责窗口、事件和绘制流程的游戏类。"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("一箭又一箭 - Arr0w Voyage")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START
        self.elapsed_time = 0.0
        self.background = self._create_background()

        self.title_font = load_font(72, bold=True)
        self.subtitle_font = load_font(28)
        self.body_font = load_font(23)
        self.button_font = load_font(28, bold=True)
        self.small_font = load_font(19)

        self.start_button = Button(pygame.Rect(0, 0, 250, 66), "开始游戏")
        self.start_button.rect.center = (WINDOW_WIDTH // 2, 445)

    def _create_background(self) -> pygame.Surface:
        """生成一次性渐变背景，避免每帧重复计算。"""
        surface = pygame.Surface(WINDOW_SIZE)
        denominator = max(WINDOW_HEIGHT - 1, 1)

        for y in range(WINDOW_HEIGHT):
            ratio = y / denominator
            color = tuple(
                int(start + (end - start) * ratio)
                for start, end in zip(BACKGROUND_TOP, BACKGROUND_BOTTOM)
            )
            pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))

        grid_layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        for x in range(0, WINDOW_WIDTH, 64):
            pygame.draw.line(grid_layer, (255, 255, 255, 32), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, 64):
            pygame.draw.line(grid_layer, (255, 255, 255, 32), (0, y), (WINDOW_WIDTH, y))
        surface.blit(grid_layer, (0, 0))
        return surface

    def run(self) -> None:
        """启动游戏主循环。"""
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(delta_time)
            self.draw()

        pygame.quit()

    def handle_events(self) -> None:
        """处理窗口、键盘和鼠标事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state is GameState.START:
                    self.running = False
                else:
                    self.state = GameState.START
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == pygame.BUTTON_LEFT
                and self.state is GameState.START
                and self.start_button.contains(event.pos)
            ):
                self.state = GameState.PLAYING

    def update(self, delta_time: float) -> None:
        """更新依赖时间的界面动画。"""
        self.elapsed_time += delta_time

    def draw(self) -> None:
        """根据当前状态绘制界面。"""
        if self.state is GameState.START:
            self._draw_start_screen()
        else:
            self._draw_playing_placeholder()

        pygame.display.flip()

    def _draw_start_screen(self) -> None:
        """绘制开始界面。"""
        self.screen.blit(self.background, (0, 0))

        panel = pygame.Rect(190, 82, 580, 480)
        shadow = panel.move(0, 10)
        pygame.draw.rect(self.screen, (184, 202, 218), shadow, border_radius=30)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=30)
        pygame.draw.rect(
            self.screen, PANEL_BORDER_COLOR, panel, width=2, border_radius=30
        )

        title = self.title_font.render("一箭又一箭", True, TITLE_COLOR)
        title_shadow = self.title_font.render("一箭又一箭", True, (197, 215, 229))
        title_shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH // 2 + 2, 205))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 202))
        self.screen.blit(title_shadow, title_shadow_rect)
        self.screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render(
            "Arr0w Voyage", True, SUBTITLE_COLOR
        )
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 264))
        self.screen.blit(subtitle, subtitle_rect)

        description = self.body_font.render(
            "观察箭头方向，规划点击顺序，让所有箭头飞出棋盘",
            True,
            TEXT_COLOR,
        )
        description_rect = description.get_rect(center=(WINDOW_WIDTH // 2, 322))
        self.screen.blit(description, description_rect)

        self._draw_direction_hint()

        mouse_position = pygame.mouse.get_pos()
        self.start_button.draw(
            self.screen, self.button_font, mouse_position, self.elapsed_time
        )

        footer = self.small_font.render(
            "鼠标点击开始游戏    ·    Esc 退出", True, MUTED_TEXT_COLOR
        )
        footer_rect = footer.get_rect(center=(WINDOW_WIDTH // 2, 520))
        self.screen.blit(footer, footer_rect)

    def _draw_direction_hint(self) -> None:
        """绘制四个方向的小箭头，强化游戏主题。"""
        labels = (("↑", (370, 372)), ("↓", (435, 372)), ("←", (500, 372)), ("→", (565, 372)))
        for label, position in labels:
            text = self.subtitle_font.render(label, True, SUBTITLE_COLOR)
            rect = text.get_rect(center=position)
            self.screen.blit(text, rect)

    def _draw_playing_placeholder(self) -> None:
        """游戏棋盘完成前使用的占位页面。"""
        self.screen.blit(self.background, (0, 0))

        title = self.body_font.render("游戏界面将在下一阶段完成", True, TITLE_COLOR)
        hint = self.small_font.render("按 Esc 返回开始界面", True, MUTED_TEXT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 290))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, 340))

        self.screen.blit(title, title_rect)
        self.screen.blit(hint, hint_rect)
