"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import copy
from enum import Enum, auto

import pygame

from levels import LEVELS
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
    draw_tool_icon,
    load_font,
)


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

BOARD_RECT = pygame.Rect(58, 132, 468, 468)
HEADER_RULE_Y = 98
FOOTER_RULE_Y = 606

CELL_BED = (222, 219, 209)
CELL_FACE = (246, 243, 235)
CELL_BORDER = (214, 213, 205)
CELL_HOVER_BORDER = (185, 166, 128)
CELL_HINT = (226, 235, 216)
CELL_BLOCKED = (248, 231, 225)
BOARD_BORDER = (157, 155, 146)

TOOL_KEYS = ("hint", "undo", "remove")
TOOL_LABELS = {
    "hint": "提示",
    "undo": "撤销",
    "remove": "移出",
}
TOOL_DESCRIPTIONS = {
    "hint": "高亮可走箭头",
    "undo": "恢复上一步",
    "remove": "移除指向箭头",
}


class GameState(Enum):
    """游戏当前所处的大状态。"""

    START = auto()
    PLAYING = auto()


class Game:
    """负责窗口、事件、游戏状态与绘制流程。"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Arr0w-voyage - 一箭又一箭")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START
        self.background = create_paper_background(WINDOW_SIZE)

        self.title_font = load_font(70, bold=True)
        self.heading_font = load_font(30, bold=True)
        self.subtitle_font = load_font(24)
        self.body_font = load_font(21)
        self.small_font = load_font(17)
        self.tiny_font = load_font(14)
        self.button_font = load_font(24, bold=True)
        self.small_button_font = load_font(18, bold=True)

        self.start_button = Button(pygame.Rect(112, 450, 210, 58), "开始游戏")
        self.restart_button = Button(
            pygame.Rect(790, 36, 122, 40),
            "重新开始",
            radius=11,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=CELL_BORDER,
            border_width=1,
        )
        self.tool_rects = {
            "hint": pygame.Rect(590, 156, 312, 56),
            "undo": pygame.Rect(590, 218, 312, 56),
            "remove": pygame.Rect(590, 280, 312, 56),
        }

        self.current_level_index = 0
        self.board: Board = copy.deepcopy(LEVELS[0])
        self.mistakes = 0
        self.max_mistakes = 3
        self.hovered_cell: tuple[int, int] | None = None
        self.feedback_cell: tuple[int, int] | None = None
        self.feedback_timer = 0.0
        self.hint_cell: tuple[int, int] | None = None
        self.hint_timer = 0.0
        self.round_finished = False
        self.message = "点击没有被挡住的箭头"
        self.history: list[tuple[int, int, str]] = []
        self.tool_uses = {key: 1 for key in TOOL_KEYS}

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

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.state is GameState.START:
            if self.start_button.contains(position):
                self.start_game()
            return

        if self.restart_button.contains(position):
            self.restart_level()
            return

        tool = self._tool_at(position)
        if tool is not None:
            self._use_tool(tool)
            return

        cell = self._cell_at(position)
        if cell is not None:
            self._click_arrow(*cell)

    def update(self, delta_time: float) -> None:
        """更新鼠标悬停、提示和短暂碰撞反馈。"""
        if self.state is GameState.PLAYING:
            self.hovered_cell = self._cell_at(pygame.mouse.get_pos())
        else:
            self.hovered_cell = None

        if self.feedback_timer > 0:
            self.feedback_timer = max(0.0, self.feedback_timer - delta_time)
            if self.feedback_timer == 0:
                self.feedback_cell = None

        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - delta_time)
            if self.hint_timer == 0:
                self.hint_cell = None

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
        self.hint_cell = None
        self.hint_timer = 0.0
        self.round_finished = False
        self.message = "点击没有被挡住的箭头"
        self.history = []
        self.tool_uses = {key: 1 for key in TOOL_KEYS}
        self.state = GameState.PLAYING

    def _click_arrow(self, row: int, col: int) -> None:
        """处理一次箭头点击，暂以即时消除配合颜色反馈。"""
        direction = self.board[row][col]
        if direction is None or self.round_finished:
            return

        if can_fly_out(self.board, row, col):
            self._remove_arrow(row, col)
            return

        self.mistakes += 1
        self.feedback_cell = (row, col)
        self.feedback_timer = 0.45

        if self.mistakes >= self.max_mistakes:
            self.round_finished = True
            self.message = "失误已用完，请重新开始"
        else:
            self.message = "前方有箭头阻挡，失误加一"

    def _remove_arrow(self, row: int, col: int) -> None:
        direction = self.board[row][col]
        if direction is None:
            return

        self.history.append((row, col, direction))
        self.board[row][col] = None
        self.feedback_cell = None
        self.hint_cell = None
        remaining = count_remaining_arrows(self.board)

        if remaining == 0:
            self.round_finished = True
            self.message = "本关已清空，通关流程将在下一阶段接入"
        else:
            self.message = f"箭头飞出，棋盘还剩 {remaining} 支"

    def _tool_at(self, position: tuple[int, int]) -> str | None:
        for tool, rect in self.tool_rects.items():
            if rect.collidepoint(position):
                return tool
        return None

    def _use_tool(self, tool: str) -> None:
        if self.round_finished:
            self.message = "本关已结束，请重新开始"
            return

        if self.tool_uses[tool] <= 0:
            self.message = "这个道具本关已经用过了"
            return

        if tool == "hint":
            self._use_hint()
        elif tool == "undo":
            self._use_undo()
        elif tool == "remove":
            self._use_remove()

    def _use_hint(self) -> None:
        for row, cells in enumerate(self.board):
            for col, direction in enumerate(cells):
                if direction is not None and can_fly_out(self.board, row, col):
                    self.tool_uses["hint"] = 0
                    self.hint_cell = (row, col)
                    self.hint_timer = 1.8
                    self.message = "提示：这一支箭头可以飞出"
                    return

        self.message = "暂时没有可直接飞出的箭头"

    def _use_undo(self) -> None:
        if not self.history:
            self.message = "现在还没有可以撤销的步骤"
            return

        row, col, direction = self.history.pop()
        self.board[row][col] = direction
        self.tool_uses["undo"] = 0
        self.hint_cell = None
        self.feedback_cell = None
        self.round_finished = False
        self.message = "已撤销上一步"

    def _use_remove(self) -> None:
        if self.hovered_cell is None:
            self.message = "先把鼠标移到要移出的箭头上"
            return

        row, col = self.hovered_cell
        if self.board[row][col] is None:
            self.message = "请把鼠标移到箭头上"
            return

        self.tool_uses["remove"] = 0
        self._remove_arrow(row, col)

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

        footer = self.small_font.render("鼠标点击开始    Esc 退出", True, INK_SOFT)
        self.screen.blit(footer, (120, 548))

        self._draw_sample_board()

    def _draw_sample_board(self) -> None:
        board = pygame.Rect(574, 168, 288, 288)
        pygame.draw.rect(
            self.screen, PAPER_DEEP, board.move(6, 7), border_radius=14
        )
        pygame.draw.rect(self.screen, PAPER_LIGHT, board, border_radius=14)
        pygame.draw.rect(
            self.screen, CELL_BORDER, board, width=2, border_radius=14
        )

        cell_size = 96
        for row in range(3):
            for col in range(3):
                cell = pygame.Rect(
                    board.left + col * cell_size + 5,
                    board.top + row * cell_size + 5,
                    cell_size - 10,
                    cell_size - 10,
                )
                pygame.draw.rect(
                    self.screen, CELL_FACE, cell, border_radius=7
                )
                pygame.draw.rect(
                    self.screen,
                    CELL_BORDER,
                    cell,
                    width=1,
                    border_radius=7,
                )

        sample_arrows = (
            (0, 1, "UP"),
            (1, 0, "RIGHT"),
            (1, 2, "LEFT"),
            (2, 1, "DOWN"),
        )
        for row, col, direction in sample_arrows:
            center = (
                board.left + col * cell_size + cell_size // 2,
                board.top + row * cell_size + cell_size // 2,
            )
            draw_arrow(self.screen, center, direction, 62)

    def _draw_game_screen(self) -> None:
        """绘制游戏 HUD、棋盘与侧边信息。"""
        self.screen.blit(self.background, (0, 0))

        brand = self.heading_font.render("Arr0w-voyage", True, INK)
        subtitle = self.small_font.render("点击式箭头解谜", True, ACCENT)
        self.screen.blit(brand, (58, 27))
        self.screen.blit(subtitle, (58, 65))

        level_text = self.subtitle_font.render(
            f"第 {self.current_level_index + 1:02d} 关  /  共 {len(LEVELS):02d} 关",
            True,
            INK_SOFT,
        )
        self.screen.blit(level_text, (372, 47))

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
            "点击箭头    Esc 返回开始界面", True, INK_SOFT
        )
        self.screen.blit(footer, (58, 617))

    def _draw_board(self) -> None:
        pygame.draw.rect(
            self.screen,
            PAPER_DEEP,
            BOARD_RECT.move(3, 5),
            border_radius=18,
        )
        pygame.draw.rect(
            self.screen, CELL_BED, BOARD_RECT, border_radius=18
        )

        rows = len(self.board)
        cols = len(self.board[0])

        for row in range(rows):
            for col in range(cols):
                direction = self.board[row][col]
                cell_rect = self._cell_rect(row, col)
                inner_rect = cell_rect.inflate(-8, -8)

                fill_color = CELL_FACE
                border_color = CELL_BORDER
                border_width = 1

                if direction is not None and self.hovered_cell == (row, col):
                    fill_color = PAPER_HOVER
                    border_color = CELL_HOVER_BORDER

                if direction is not None and self.hint_cell == (row, col):
                    fill_color = CELL_HINT
                    border_color = MOSS
                    border_width = 2

                if self.feedback_cell == (row, col):
                    fill_color = CELL_BLOCKED
                    border_color = ACCENT
                    border_width = 2

                pygame.draw.rect(
                    self.screen,
                    fill_color,
                    inner_rect,
                    border_radius=7,
                )
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    inner_rect,
                    width=border_width,
                    border_radius=7,
                )

                if direction is None:
                    pygame.draw.circle(
                        self.screen, CELL_BORDER, inner_rect.center, 2
                    )
                    continue

                arrow_offset = 0
                if self.feedback_cell == (row, col):
                    arrow_offset = 3 if self.feedback_timer > 0.22 else -3

                draw_arrow(
                    self.screen,
                    inner_rect.center,
                    direction,
                    int(min(inner_rect.width, inner_rect.height) * 0.72),
                    offset=arrow_offset,
                )

        pygame.draw.rect(
            self.screen,
            BOARD_BORDER,
            BOARD_RECT,
            width=2,
            border_radius=18,
        )

    def _draw_sidebar(self) -> None:
        left = 590
        tools_title = self.small_font.render("每关一次 / 道具", True, INK_SOFT)
        self.screen.blit(tools_title, (left, 136))

        mouse_position = pygame.mouse.get_pos()
        for tool in TOOL_KEYS:
            self._draw_tool_button(tool, mouse_position)

        pygame.draw.line(self.screen, RULE, (left, 350), (902, 350), 1)

        guide_lines = (
            "点按箭头，让它可以飞出棋盘。",
            "前方有箭头时，本次点击算作失误。",
        )
        for index, text in enumerate(guide_lines):
            line = self.small_font.render(text, True, INK_SOFT)
            self.screen.blit(line, (left, 368 + index * 28))

        remaining = count_remaining_arrows(self.board)
        self._draw_status_row("剩余箭头", f"{remaining:02d}", 424)
        self._draw_status_row(
            "剩余失误次数", f"{self.max_mistakes - self.mistakes:02d}", 488
        )

        message_color = INK
        if self.round_finished:
            message_color = MOSS if remaining == 0 else ACCENT

        message = self.small_font.render(self.message, True, message_color)
        self.screen.blit(message, (left, 560))

    def _draw_tool_button(
        self, tool: str, mouse_position: tuple[int, int]
    ) -> None:
        rect = self.tool_rects[tool]
        used = self.tool_uses[tool] <= 0
        hovered = not used and rect.collidepoint(mouse_position)

        if used:
            fill_color = (228, 227, 222)
            border_color = (205, 204, 199)
            icon_color = (155, 155, 151)
            title_color = (126, 126, 122)
            description_color = (158, 158, 154)
        else:
            fill_color = PAPER_HOVER if hovered else CELL_FACE
            border_color = CELL_HOVER_BORDER if hovered else RULE
            icon_color = MOSS
            title_color = INK
            description_color = INK_SOFT

        pygame.draw.rect(self.screen, fill_color, rect, border_radius=10)
        pygame.draw.rect(
            self.screen,
            border_color,
            rect,
            width=1,
            border_radius=10,
        )

        icon_center = (rect.left + 31, rect.centery)
        draw_tool_icon(self.screen, tool, icon_center, icon_color)

        label = self.body_font.render(TOOL_LABELS[tool], True, title_color)
        label_rect = label.get_rect(
            midleft=(rect.left + 58, rect.top + 19)
        )
        self.screen.blit(label, label_rect)

        description = self.tiny_font.render(
            TOOL_DESCRIPTIONS[tool], True, description_color
        )
        description_rect = description.get_rect(
            midleft=(rect.left + 58, rect.top + 39)
        )
        self.screen.blit(description, description_rect)

        if used:
            status = self.tiny_font.render("已使用", True, description_color)
            status_rect = status.get_rect(
                midright=(rect.right - 14, rect.centery)
            )
            self.screen.blit(status, status_rect)
    def _draw_status_row(self, label: str, value: str, top: int) -> None:
        left = 590
        label_text = self.small_font.render(label, True, INK_SOFT)
        value_text = self.heading_font.render(value, True, INK)
        self.screen.blit(label_text, (left, top + 6))
        value_rect = value_text.get_rect(topright=(902, top))
        self.screen.blit(value_text, value_rect)
        pygame.draw.line(self.screen, RULE, (left, top + 54), (902, top + 54), 1)
