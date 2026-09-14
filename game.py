"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import copy
from enum import Enum, auto

import pygame

from animations import AnimationState
from audio import AudioManager
from levels import LEVELS
from logic import Board, can_fly_out, count_remaining_arrows
from tools import TOOL_DESCRIPTIONS, TOOL_KEYS, TOOL_LABELS, ToolId, ToolState
from ui import (
    ACCENT,
    DIRECTION_VECTORS,
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
    draw_heart,
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



class GameState(Enum):
    """游戏当前所处的大状态。"""

    START = auto()
    PLAYING = auto()
    LEVEL_COMPLETE = auto()
    GAME_COMPLETE = auto()
    LOSE = auto()


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
        self.start_subtitle_font = load_font(36, bold=True)
        self.body_font = load_font(21)
        self.small_font = load_font(17)
        self.tiny_font = load_font(14)
        self.button_font = load_font(24, bold=True)
        self.small_button_font = load_font(18, bold=True)

        self.start_button = Button(pygame.Rect(112, 450, 210, 58), "开始游戏")
        self.restart_button = Button(
            pygame.Rect(646, 36, 122, 40),
            "重新开始",
            radius=11,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=CELL_BORDER,
            border_width=1,
        )
        self.exit_button = Button(
            pygame.Rect(780, 36, 122, 40),
            "退出游戏",
            radius=11,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=CELL_BORDER,
            border_width=1,
        )
        self.result_primary_button = Button(
            pygame.Rect(310, 410, 220, 58),
            "进入下一关",
            radius=12,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=CELL_BORDER,
            border_width=1,
        )
        self.result_secondary_button = Button(
            pygame.Rect(550, 410, 200, 58),
            "返回首页",
            radius=12,
            normal_fill=PAPER_LIGHT,
            hover_fill=PAPER_HOVER,
            normal_text=INK,
            hover_text=INK,
            border_color=CELL_BORDER,
            border_width=1,
        )
        self.tool_rects = {
            ToolId.HINT: pygame.Rect(590, 162, 312, 56),
            ToolId.EXTRA_MISTAKE: pygame.Rect(590, 222, 312, 56),
            ToolId.REMOVE: pygame.Rect(590, 282, 312, 56),
        }

        self.current_level_index = 0
        self.board: Board = copy.deepcopy(LEVELS[0])
        self.mistakes = 0
        self.max_mistakes = 3
        self.hovered_cell: tuple[int, int] | None = None
        self.effects = AnimationState()
        self.tools = ToolState()
        self.audio = AudioManager()
        self.round_finished = False
        self.pending_result: GameState | None = None
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

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.state is GameState.START:
            if self.start_button.contains(position):
                self.start_game()
            return

        if self.state is not GameState.PLAYING:
            self._handle_result_click(position)
            return

        if self.restart_button.contains(position):
            self.restart_level()
            return

        if self.exit_button.contains(position):
            self.running = False
            return

        tool = self._tool_at(position)
        if tool is not None:
            self._use_tool(tool)
            return

        cell = self._cell_at(position)
        if cell is not None:
            self._click_arrow(*cell)

    def _handle_result_click(self, position: tuple[int, int]) -> None:
        """处理通关或失败界面中的按钮。"""
        if self.result_secondary_button.contains(position):
            self.return_to_start()
            return

        if not self.result_primary_button.contains(position):
            return

        if self.state is GameState.LEVEL_COMPLETE:
            self.next_level()
        elif self.state is GameState.GAME_COMPLETE:
            self.start_game()
        elif self.state is GameState.LOSE:
            self.restart_level()

    def update(self, delta_time: float) -> None:
        """更新鼠标悬停、提示和短暂碰撞反馈。"""
        if self.state is GameState.PLAYING:
            self.hovered_cell = self._cell_at(pygame.mouse.get_pos())
        else:
            self.hovered_cell = None

        self.effects.update(delta_time)
        if (
            self.state is GameState.PLAYING
            and self.round_finished
            and self.pending_result is not None
            and not self.effects.has_flying_arrows
            and self.effects.feedback_timer <= 0
        ):
            self.state = self.pending_result
            self.pending_result = None

    def start_game(self) -> None:
        """从第一关开始游戏。"""
        self.current_level_index = 0
        self._load_level(reset_tools=True, reset_mistakes=True)

    def next_level(self) -> None:
        """进入下一关。"""
        if self.current_level_index + 1 < len(LEVELS):
            self.current_level_index += 1
            self._load_level()

    def return_to_start(self) -> None:
        """返回开始界面。"""
        self.state = GameState.START
        self.round_finished = False
        self.pending_result = None
        self.hovered_cell = None
        self.effects.reset()

    def restart_level(self) -> None:
        """重新开始整局游戏，并回到第一关。"""
        self.current_level_index = 0
        self._load_level(reset_tools=True, reset_mistakes=True)

    def _load_level(
        self,
        *,
        reset_tools: bool = False,
        reset_mistakes: bool = False,
    ) -> None:
        self.board = copy.deepcopy(LEVELS[self.current_level_index])
        self.max_mistakes = 3
        if reset_mistakes:
            self.mistakes = 0
        self.hovered_cell = None
        self.effects.reset()
        if reset_tools:
            self.tools.reset()
        else:
            self.tools.cancel_selection()
        self.round_finished = False
        self.pending_result = None
        self.message = "点击没有被挡住的箭头"
        self.state = GameState.PLAYING

    def _click_arrow(self, row: int, col: int) -> None:
        """处理一次箭头点击。"""
        direction = self.board[row][col]
        if direction is None or self.round_finished:
            return

        if self.tools.pending is ToolId.REMOVE:
            self.tools.consume(ToolId.REMOVE)
            self.tools.cancel_selection()
            self._remove_arrow(row, col, animate=False)
            return

        if can_fly_out(self.board, row, col):
            self._remove_arrow(row, col)
            return

        self.mistakes += 1
        self.effects.show_feedback((row, col))
        self.audio.play("blocked")

        if self.mistakes >= self.max_mistakes:
            self.round_finished = True
            self.pending_result = GameState.LOSE
            self.message = "失误已用完，请重新开始"
        else:
            self.effects.show_toast("前方有箭头阻挡，失误加一", duration=1.0)
            self.message = "前方有箭头阻挡，失误加一"

    def _remove_arrow(
        self,
        row: int,
        col: int,
        *,
        animate: bool = True,
    ) -> None:
        direction = self.board[row][col]
        if direction is None:
            return

        if animate:
            self.effects.start_fly((row, col), direction)
        self.board[row][col] = None
        self.tools.cancel_selection()
        self.effects.clear_feedback()
        self.effects.clear_hint()
        remaining = count_remaining_arrows(self.board)

        if remaining == 0:
            self.round_finished = True
            self.audio.play("win")
            if self.current_level_index == len(LEVELS) - 1:
                self.pending_result = GameState.GAME_COMPLETE
                self.message = "最后一关已清空，全部通关"
            else:
                self.pending_result = GameState.LEVEL_COMPLETE
                self.message = "本关已清空，准备进入下一关"
        else:
            action = "飞出" if animate else "移出"
            self.message = f"箭头{action}，棋盘还剩 {remaining} 支"
            self.audio.play("fly")

    def _tool_at(self, position: tuple[int, int]) -> ToolId | None:
        for tool, rect in self.tool_rects.items():
            if rect.collidepoint(position):
                return tool
        return None

    def _use_tool(self, tool: ToolId) -> None:
        if self.round_finished:
            self.message = "本关已结束，请重新开始"
            return

        if tool is not ToolId.REMOVE and self.tools.pending is not None:
            self.tools.cancel_selection()

        if self.tools.is_used(tool):
            self.message = "这个道具本关已经用过了"
            return

        if tool is ToolId.HINT:
            self._use_hint()
        elif tool is ToolId.EXTRA_MISTAKE:
            self._use_extra_mistake()
        elif tool is ToolId.REMOVE:
            self._use_remove()

    def _use_hint(self) -> None:
        for row, cells in enumerate(self.board):
            for col, direction in enumerate(cells):
                if direction is not None and can_fly_out(self.board, row, col):
                    self.tools.consume(ToolId.HINT)
                    self.effects.show_hint((row, col))
                    self.message = "提示：这一支箭头可以飞出"
                    self.audio.play("hint")
                    return

        self.message = "暂时没有可直接飞出的箭头"

    def _use_extra_mistake(self) -> None:
        if self.mistakes == 0:
            self.message = "当前是满血状态，暂时不能使用"
            self.effects.show_toast("满血状态，不能使用增加失误次数")
            return

        self.mistakes -= 1
        self.tools.consume(ToolId.EXTRA_MISTAKE)
        self.message = "恢复一颗红心"
        self.effects.show_toast("恢复一颗红心")
        self.audio.play("heal")

    def _use_remove(self) -> None:
        self.tools.begin_selection(ToolId.REMOVE)
        self.message = "请点击要移出的箭头"
        self.audio.play("remove")
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
        elif self.state is GameState.PLAYING:
            self._draw_game_screen()
        else:
            self._draw_result_screen()

        pygame.display.flip()

    def _draw_start_screen(self) -> None:
        """绘制偏印刷海报风格的开始界面。"""
        self.screen.blit(self.background, (0, 0))

        pygame.draw.line(self.screen, ACCENT, (84, 82), (84, 544), 3)
        pygame.draw.circle(self.screen, ACCENT, (84, 82), 5)

        title = self.title_font.render("Arr0w-voyage", True, INK)
        self.screen.blit(title, (116, 68))

        subtitle = self.start_subtitle_font.render("一箭又一箭", True, ACCENT)
        self.screen.blit(subtitle, (120, 160))

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
        self.exit_button.draw(
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
        self._draw_toast()

    def _draw_result_screen(self) -> None:
        """绘制关卡完成、全部通关和失败结果界面。"""
        self.screen.blit(self.background, (0, 0))

        is_success = self.state in (
            GameState.LEVEL_COMPLETE,
            GameState.GAME_COMPLETE,
        )
        accent = MOSS if is_success else ACCENT
        if self.state is GameState.LEVEL_COMPLETE:
            kicker = "LEVEL COMPLETE"
            title = "本关通过"
            description = "棋盘已经清空，下一关正等着你。"
            primary_text = "进入下一关"
        elif self.state is GameState.GAME_COMPLETE:
            kicker = "ALL CLEAR"
            title = "全部通关"
            description = "三关全部清空，最后一支箭也顺利离场。"
            primary_text = "再玩一遍"
        else:
            kicker = "TRY AGAIN"
            title = "本关失败"
            description = "失误次数已经用完，重新整理思路再出发。"
            primary_text = "重新开始"

        pygame.draw.line(self.screen, accent, (100, 108), (100, 500), 3)
        pygame.draw.circle(self.screen, accent, (100, 108), 5)

        brand = self.small_font.render("Arr0w-voyage", True, INK_SOFT)
        self.screen.blit(brand, (128, 98))

        kicker_text = self.small_font.render(kicker, True, accent)
        self.screen.blit(kicker_text, (130, 160))

        title_text = self.title_font.render(title, True, INK)
        self.screen.blit(title_text, (126, 198))

        description_text = self.subtitle_font.render(description, True, INK_SOFT)
        self.screen.blit(description_text, (130, 292))

        remaining = count_remaining_arrows(self.board)
        mistakes_left = max(0, self.max_mistakes - self.mistakes)
        stats_rect = pygame.Rect(132, 342, 728, 46)
        pygame.draw.rect(self.screen, PAPER_LIGHT, stats_rect, border_radius=10)
        stats = (
            f"第 {self.current_level_index + 1:02d} 关   |   "
            f"剩余箭头 {remaining:02d}   |   "
            f"剩余失误 {mistakes_left}"
        )
        stats_text = self.body_font.render(stats, True, INK)
        stats_rect_text = stats_text.get_rect(center=stats_rect.center)
        self.screen.blit(stats_text, stats_rect_text)

        self.result_primary_button.text = primary_text
        mouse_position = pygame.mouse.get_pos()
        self.result_primary_button.draw(
            self.screen, self.small_button_font, mouse_position
        )
        self.result_secondary_button.draw(
            self.screen, self.small_button_font, mouse_position
        )


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

                if direction is not None and self.tools.pending is ToolId.REMOVE:
                    fill_color = CELL_HINT
                    border_color = MOSS

                if direction is not None and self.effects.hint_cell == (row, col):
                    fill_color = CELL_HINT
                    border_color = MOSS
                    border_width = 2

                if self.effects.feedback_cell == (row, col):
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
                if self.effects.feedback_cell == (row, col):
                    arrow_offset = 3 if self.effects.feedback_timer > 0.22 else -3

                draw_arrow(
                    self.screen,
                    inner_rect.center,
                    direction,
                    int(min(inner_rect.width, inner_rect.height) * 0.72),
                    offset=arrow_offset,
                )

        self._draw_flying_arrows()

        pygame.draw.rect(
            self.screen,
            BOARD_BORDER,
            BOARD_RECT,
            width=2,
            border_radius=18,
        )

    def _draw_flying_arrows(self) -> None:
        """绘制正在离开棋盘的箭头。"""
        rows = len(self.board)
        cols = len(self.board[0])
        cell_width = BOARD_RECT.width / cols
        cell_height = BOARD_RECT.height / rows
        base_size = min(cell_width, cell_height) * 0.72

        for arrow in self.effects.flying_arrows:
            start_x, start_y = self._cell_rect(arrow.row, arrow.col).center
            vector_x, vector_y = DIRECTION_VECTORS[arrow.direction]

            if vector_x > 0:
                distance = BOARD_RECT.right - start_x + 100
            elif vector_x < 0:
                distance = start_x - BOARD_RECT.left + 100
            elif vector_y > 0:
                distance = BOARD_RECT.bottom - start_y + 100
            else:
                distance = start_y - BOARD_RECT.top + 100

            progress = arrow.progress
            center = (
                int(start_x + vector_x * distance * progress),
                int(start_y + vector_y * distance * progress),
            )
            size = max(12, int(base_size * (1.0 - progress * 0.30)))
            draw_arrow(self.screen, center, arrow.direction, size)

    def _draw_sidebar(self) -> None:
        left = 590
        tools_title = self.small_font.render("道具", True, INK_SOFT)
        self.screen.blit(tools_title, (left, 120))

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
        self._draw_heart_row(488)

        message_color = INK
        if self.round_finished:
            message_color = MOSS if remaining == 0 else ACCENT

        message = self.small_font.render(self.message, True, message_color)
        self.screen.blit(message, (left, 560))

    def _draw_tool_button(
        self, tool: ToolId, mouse_position: tuple[int, int]
    ) -> None:
        rect = self.tool_rects[tool]
        used = self.tools.is_used(tool)
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
        draw_tool_icon(self.screen, tool.value, icon_center, icon_color)

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

        status_text = f"X{self.tools.remaining[tool]}"
        status = self.tiny_font.render(status_text, True, description_color)
        status_rect = status.get_rect(
            midright=(rect.right - 14, rect.centery)
        )
        self.screen.blit(status, status_rect)

    def _draw_heart_row(self, top: int) -> None:
        left = 590
        label = self.small_font.render("剩余失误", True, INK_SOFT)
        self.screen.blit(label, (left, top + 6))

        remaining = max(0, self.max_mistakes - self.mistakes)
        for index in range(self.max_mistakes):
            center = (770 + index * 48, top + 22)
            color = ACCENT if index < remaining else (191, 190, 186)
            draw_heart(self.screen, center, 30, color)

        pygame.draw.line(self.screen, RULE, (left, top + 54), (902, top + 54), 1)

    def _draw_toast(self) -> None:
        if self.effects.toast_text is None:
            return

        text = self.small_font.render(self.effects.toast_text, True, PAPER_LIGHT)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 113))
        box_rect = text_rect.inflate(34, 18)
        pygame.draw.rect(self.screen, INK, box_rect, border_radius=10)
        self.screen.blit(text, text_rect)

    def _draw_status_row(self, label: str, value: str, top: int) -> None:
        left = 590
        label_text = self.small_font.render(label, True, INK_SOFT)
        value_text = self.heading_font.render(value, True, INK)
        self.screen.blit(label_text, (left, top + 6))
        value_rect = value_text.get_rect(topright=(902, top))
        self.screen.blit(value_text, value_rect)
        pygame.draw.line(self.screen, RULE, (left, top + 54), (902, top + 54), 1)
