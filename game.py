"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import copy
from enum import Enum, auto

import pygame

from levels import LEVEL_NAMES, LEVELS
from logic import Board, can_fly_out, count_remaining_arrows
from ui import (
    ACCENT,
    INK,
    INK_SOFT,
    MOSS,
    PAPER_DEEP,
    PAPER_HOVER,
    PAPER_LIGHT,
    RULE,
    Button,
    create_paper_background,
    draw_arrow,
    load_font,
)


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

BOARD_RECT = pygame.Rect(58, 132, 468, 468)
HEADER_RULE_Y = 98
FOOTER_RULE_Y = 606


class GameState(Enum):
    """游戏当前所处的大状态。"""

    START = auto()
    PLAYING = auto()


class Game:
    """负责窗口、事件、游戏状态与绘制流程。"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("一箭又一箭 - Arr0w Voyage")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START
        self.background = create_paper_background(WINDOW_SIZE)

        self.title_font = load_font(70, bold=True)
        self.heading_font = load_font(34, bold=True)
        self.level_number_font = load_font(72, bold=True)
        self.subtitle_font = load_font(24)
        self.body_font = load_font(21)
        self.small_font = load_font(17)
        self.button_font = load_font(24, bold=True)
        self.small_button_font = load_font(18, bold=True)

        self.start_button = Button(pygame.Rect(112, 450, 210, 58), "开始游戏")
        self.restart_button = Button(
            pygame.Rect(790, 36, 122, 40), "重新开始"
        )

        self.current_level_index = 0
        self.board: Board = copy.deepcopy(LEVELS[0])
        self.mistakes = 0
        self.max_mistakes = 3
        self.hovered_cell: tuple[int, int] | None = None
        self.feedback_cell: tuple[int, int] | None = None
        self.feedback_timer = 0.0
        self.round_finished = False
        self.message = "点击没有被挡住的箭头"

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
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.state is GameState.START:
                self.running = False
            else:
                self.state = GameState.START
        elif key == pygame.K_r and self.state is GameState.PLAYING:
            self.restart_level()

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.state is GameState.START:
            if self.start_button.contains(position):
                self.start_game()
            return

        if self.restart_button.contains(position):
            self.restart_level()
            return

        cell = self._cell_at(position)
        if cell is not None:
            self._click_arrow(*cell)

    def update(self, delta_time: float) -> None:
        """更新鼠标悬停和短暂碰撞反馈。"""
        if self.state is GameState.PLAYING:
            self.hovered_cell = self._cell_at(pygame.mouse.get_pos())
        else:
            self.hovered_cell = None

        if self.feedback_timer > 0:
            self.feedback_timer = max(0.0, self.feedback_timer - delta_time)
            if self.feedback_timer == 0:
                self.feedback_cell = None

    def start_game(self) -> None:
        """从第一关开始游戏。"""
        self.current_level_index = 0
        self._load_level()

    def restart_level(self) -> None:
        """恢复当前关卡的初始状态。"""
        self._load_level()

    def _load_level(self) -> None:
        self.board = copy.deepcopy(LEVELS[self.current_level_index])
        self.mistakes = 0
        self.hovered_cell = None
        self.feedback_cell = None
        self.feedback_timer = 0.0
        self.round_finished = False
        self.message = "点击没有被挡住的箭头"
        self.state = GameState.PLAYING

    def _click_arrow(self, row: int, col: int) -> None:
        """处理一次箭头点击，暂以即时消除配合颜色反馈。"""
        direction = self.board[row][col]
        if direction is None or self.round_finished:
            return

        if can_fly_out(self.board, row, col):
            self.board[row][col] = None
            remaining = count_remaining_arrows(self.board)
            self.feedback_cell = None

            if remaining == 0:
                self.round_finished = True
                self.message = "本关已清空，通关流程将在下一阶段接入"
            else:
                self.message = f"箭头飞出，棋盘还剩 {remaining} 支"
            return

        self.mistakes += 1
        self.feedback_cell = (row, col)
        self.feedback_timer = 0.45

        if self.mistakes >= self.max_mistakes:
            self.round_finished = True
            self.message = "失误已用完，按 R 或重新开始"
        else:
            self.message = "前方有箭头阻挡，失误加一"

    def _cell_at(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not BOARD_RECT.collidepoint(position):
            return None

        rows = len(self.board)
        cols = len(self.board[0])
        cell_width = BOARD_RECT.width / cols
        cell_height = BOARD_RECT.height / rows
        col = int((position[0] - BOARD_RECT.left) / cell_width)
        row = int((position[1] - BOARD_RECT.top) / cell_height)

        if 0 <= row < rows and 0 <= col < cols:
            return row, col
        return None

    def _cell_rect(self, row: int, col: int) -> pygame.Rect:
        rows = len(self.board)
        cols = len(self.board[0])
        left = BOARD_RECT.left + round(col * BOARD_RECT.width / cols)
        top = BOARD_RECT.top + round(row * BOARD_RECT.height / rows)
        right = BOARD_RECT.left + round((col + 1) * BOARD_RECT.width / cols)
        bottom = BOARD_RECT.top + round((row + 1) * BOARD_RECT.height / rows)
        return pygame.Rect(left, top, right - left, bottom - top)

    def draw(self) -> None:
        """根据当前状态绘制界面。"""
        if self.state is GameState.START:
            self._draw_start_screen()
        else:
            self._draw_game_screen()

        pygame.display.flip()

    def _draw_start_screen(self) -> None:
        """绘制偏印刷海报风格的开始界面。"""
        self.screen.blit(self.background, (0, 0))

        pygame.draw.line(self.screen, ACCENT, (84, 82), (84, 544), 3)
        pygame.draw.circle(self.screen, ACCENT, (84, 82), 5)

        title = self.title_font.render("一箭又一箭", True, INK)
        self.screen.blit(title, (116, 88))

        subtitle = self.subtitle_font.render("点击式箭头解谜", True, ACCENT)
        self.screen.blit(subtitle, (120, 174))

        line = self.body_font.render(
            "观察箭头方向，找到一条通向棋盘外的路。", True, INK_SOFT
        )
        self.screen.blit(line, (120, 226))

        tips = (
            "01  找出前方没有阻挡的箭头",
            "02  规划顺序，避免无路可走",
            "03  清空棋盘，进入下一关",
        )
        for index, tip in enumerate(tips):
            text = self.small_font.render(tip, True, INK)
            self.screen.blit(text, (120, 292 + index * 38))

        mouse_position = pygame.mouse.get_pos()
        self.start_button.draw(self.screen, self.button_font, mouse_position)

        footer = self.small_font.render(
            "鼠标选择    R 重新开始    Esc 返回", True, INK_SOFT
        )
        self.screen.blit(footer, (120, 548))

        self._draw_sample_board()

    def _draw_sample_board(self) -> None:
        board = pygame.Rect(574, 168, 288, 288)
        pygame.draw.rect(self.screen, PAPER_DEEP, board.move(6, 7))
        pygame.draw.rect(self.screen, PAPER_LIGHT, board)
        pygame.draw.rect(self.screen, INK, board, width=2)

        for offset in (96, 192):
            pygame.draw.line(
                self.screen, RULE, (board.left + offset, board.top),
                (board.left + offset, board.bottom), 1
            )
            pygame.draw.line(
                self.screen, RULE, (board.left, board.top + offset),
                (board.right, board.top + offset), 1
            )

        sample_arrows = (
            (0, 1, "UP"),
            (1, 0, "RIGHT"),
            (1, 2, "LEFT"),
            (2, 1, "DOWN"),
        )
        for row, col, direction in sample_arrows:
            center = (
                board.left + col * 96 + 48,
                board.top + row * 96 + 48,
            )
            draw_arrow(self.screen, center, direction, 66)

    def _draw_game_screen(self) -> None:
        """绘制游戏 HUD、棋盘与侧边信息。"""
        self.screen.blit(self.background, (0, 0))

        brand = self.body_font.render("一箭又一箭", True, INK)
        edition = self.small_font.render("点击式箭头解谜", True, ACCENT)
        self.screen.blit(brand, (58, 30))
        self.screen.blit(edition, (58, 61))

        level_text = self.subtitle_font.render(
            f"第 {self.current_level_index + 1:02d} 关  /  共 {len(LEVELS):02d} 关",
            True,
            INK_SOFT,
        )
        self.screen.blit(level_text, (370, 47))

        mouse_position = pygame.mouse.get_pos()
        self.restart_button.draw(
            self.screen, self.small_button_font, mouse_position
        )

        pygame.draw.line(
            self.screen, INK, (58, HEADER_RULE_Y), (902, HEADER_RULE_Y), 1
        )
        pygame.draw.line(
            self.screen, RULE, (58, FOOTER_RULE_Y), (902, FOOTER_RULE_Y), 1
        )

        self._draw_board()
        self._draw_sidebar()

        footer = self.small_font.render(
            "点击箭头    R 重新开始    Esc 返回开始界面", True, INK_SOFT
        )
        self.screen.blit(footer, (58, 617))

    def _draw_board(self) -> None:
        pygame.draw.rect(self.screen, PAPER_DEEP, BOARD_RECT.move(6, 7))
        pygame.draw.rect(self.screen, PAPER_LIGHT, BOARD_RECT)
        pygame.draw.rect(self.screen, INK, BOARD_RECT, width=2)

        rows = len(self.board)
        cols = len(self.board[0])

        for col in range(1, cols):
            x = BOARD_RECT.left + round(col * BOARD_RECT.width / cols)
            pygame.draw.line(
                self.screen, RULE, (x, BOARD_RECT.top), (x, BOARD_RECT.bottom), 1
            )
        for row in range(1, rows):
            y = BOARD_RECT.top + round(row * BOARD_RECT.height / rows)
            pygame.draw.line(
                self.screen, RULE, (BOARD_RECT.left, y), (BOARD_RECT.right, y), 1
            )

        for row in range(rows):
            for col in range(cols):
                direction = self.board[row][col]
                cell_rect = self._cell_rect(row, col)
                center = cell_rect.center

                if direction is None:
                    pygame.draw.circle(self.screen, RULE, center, 2)
                    continue

                if self.hovered_cell == (row, col):
                    pygame.draw.rect(self.screen, PAPER_HOVER, cell_rect)
                    pygame.draw.rect(self.screen, ACCENT, cell_rect, width=2)

                arrow_offset = 0
                if self.feedback_cell == (row, col):
                    pygame.draw.rect(self.screen, ACCENT, cell_rect, width=4)
                    arrow_offset = 3 if self.feedback_timer > 0.22 else -3

                draw_arrow(
                    self.screen,
                    center,
                    direction,
                    int(min(cell_rect.width, cell_rect.height) * 0.72),
                    offset=arrow_offset,
                )

    def _draw_sidebar(self) -> None:
        left = 590
        number = self.level_number_font.render(
            f"{self.current_level_index + 1:02d}", True, INK
        )
        self.screen.blit(number, (left, 142))

        level_name = self.heading_font.render(
            LEVEL_NAMES[self.current_level_index], True, INK
        )
        self.screen.blit(level_name, (left, 232))

        pygame.draw.line(self.screen, RULE, (left, 286), (902, 286), 1)

        guide_lines = (
            "点按箭头，让它可以飞出棋盘。",
            "如果前方有箭头，本次点击算作失误。",
        )
        for index, text in enumerate(guide_lines):
            line = self.small_font.render(text, True, INK_SOFT)
            self.screen.blit(line, (left, 312 + index * 30))

        remaining = count_remaining_arrows(self.board)
        self._draw_status_row("剩余箭头", f"{remaining:02d}", 390)
        self._draw_status_row(
            "剩余失误", f"{self.max_mistakes - self.mistakes:02d}", 450
        )

        message_color = INK
        if self.round_finished:
            message_color = MOSS if remaining == 0 else ACCENT

        message = self.small_font.render(self.message, True, message_color)
        self.screen.blit(message, (left, 538))

    def _draw_status_row(self, label: str, value: str, top: int) -> None:
        left = 590
        label_text = self.small_font.render(label, True, INK_SOFT)
        value_text = self.heading_font.render(value, True, INK)
        self.screen.blit(label_text, (left, top + 8))
        value_rect = value_text.get_rect(topright=(902, top))
        self.screen.blit(value_text, value_rect)
        pygame.draw.line(self.screen, RULE, (left, top + 54), (902, top + 54), 1)
