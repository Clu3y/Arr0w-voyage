"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import pygame


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
BACKGROUND_COLOR = (238, 242, 247)
TITLE_COLOR = (31, 41, 55)
HINT_COLOR = (75, 85, 99)


class Game:
    """负责窗口、事件和绘制流程的游戏类。"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Arr0w Voyage - 一箭又一箭")
        self.clock = pygame.time.Clock()
        self.running = True
        self.title_font = pygame.font.Font(None, 42)
        self.hint_font = pygame.font.Font(None, 22)

    def run(self) -> None:
        """启动游戏主循环。"""
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(delta_time)
            self.draw()

        pygame.quit()

    def handle_events(self) -> None:
        """处理窗口和键盘事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self, delta_time: float) -> None:
        """更新游戏状态；后续阶段将在这里推进动画。"""
        _ = delta_time

    def draw(self) -> None:
        """绘制当前帧。"""
        self.screen.fill(BACKGROUND_COLOR)

        title = self.title_font.render("Arr0w Voyage", True, TITLE_COLOR)
        hint = self.hint_font.render(
            "Project scaffold is running. Press Esc to exit.", True, HINT_COLOR
        )
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 250))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, 330))

        self.screen.blit(title, title_rect)
        self.screen.blit(hint, hint_rect)
        pygame.display.flip()
