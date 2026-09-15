"""Pygame 游戏主循环与界面管理。"""

from __future__ import annotations

import copy
import webbrowser
from enum import Enum, auto

import pygame

from animations import AnimationState
from audio import AudioManager
from levels import LEVELS
from logic import Board, can_fly_out, count_remaining_arrows
from tools import TOOL_DESCRIPTIONS, TOOL_KEYS, ToolId, ToolState
from ui import (
    ACCENT,
    DIALOG_BUTTON_ASSET,
    DIALOG_CLOSE_ASSET,
    DIALOG_HEADER_ASSET,
    DIALOG_PANEL_ASSET,
    DIRECTION_VECTORS,
    GAME_LOGO_FILE,
    GAME_SCREEN_BACKGROUND_ASSET,
    GITHUB_ICON_FILE,
    INK,
    INK_SOFT,
    MOSS,
    PAPER_DEEP,
    PAPER_HOVER,
    PAPER_LIGHT,
    RULE,
    START_LOGO_FILE,
    TOOL_FRAME_ASSET,
    Button,
    create_paper_background,
    draw_arrow,
    draw_cell_texture,
    draw_github_icon,
    draw_heart,
    draw_tool_icon,
    get_scaled_background_asset,
    get_cropped_scaled_ui_asset,
    get_nine_slice_background,
    load_font,
    set_custom_cursor,
)


AUTHOR_NAME = "Clu3y"
REPOSITORY_URL = "https://github.com/Clu3y/Arr0w-voyage"


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

BOARD_RECT = pygame.Rect(58, 132, 468, 468)
HEADER_RULE_Y = 98
FOOTER_RULE_Y = 606

CELL_BED = (216, 201, 177)
CELL_FACE = (245, 236, 218)
CELL_BORDER = (207, 190, 163)
CELL_HOVER_BORDER = (171, 142, 99)
CELL_HINT = (222, 231, 207)
CELL_BLOCKED = (244, 219, 207)
BOARD_BORDER = (141, 124, 99)



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
        set_custom_cursor()
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START
        self.background = create_paper_background(WINDOW_SIZE)
        self.game_background = (
            get_nine_slice_background(
                GAME_SCREEN_BACKGROUND_ASSET,
                WINDOW_SIZE,
                (40, 20, 40, 20),
            )
            or self.background
        )

        self.title_font = load_font(70, bold=True)
        self.heading_font = load_font(30, bold=True)
        self.subtitle_font = load_font(24)
        self.start_subtitle_font = load_font(36, bold=True)
        self.body_font = load_font(21)
        self.small_font = load_font(17)
        self.tiny_font = load_font(14)
        self.button_font = load_font(24, bold=True)
        self.small_button_font = load_font(18, bold=True)

        self.start_button = Button(pygame.Rect(112, 440, 210, 52), "开始游戏")
        self.custom_mode_button = Button(
            pygame.Rect(112, 508, 210, 52),
            "自定义模式",
        )
        self.author_link_rect = pygame.Rect(690, 574, 220, 38)
        self.restart_button = Button(
            pygame.Rect(600, 42, 150, 48),
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
            pygame.Rect(760, 42, 150, 48),
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
        self.dialog_panel_rect = pygame.Rect(200, 190, 560, 280)
        self.dialog_header_rect = pygame.Rect(280, 140, 400, 100)
        self.dialog_close_rect = pygame.Rect(712, 198, 48, 48)
        self.dialog_confirm_rect = pygame.Rect(310, 395, 150, 50)
        self.dialog_cancel_rect = pygame.Rect(500, 395, 150, 50)
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
        self.audio.play_music("bgm")
        self.hover_target: str | None = None
        self.dialog_action: str | None = None
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
            if self.dialog_action is not None:
                self.dialog_action = None
                self.hover_target = None
                return
            if self.state is GameState.START:
                self.running = False
            else:
                self.state = GameState.START

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.dialog_action is not None:
            self._handle_dialog_click(position)
            return

        if self.state is GameState.START:
            if self.start_button.contains(position):
                self.start_game()
            elif self.custom_mode_button.contains(position):
                return
            elif self.author_link_rect.collidepoint(position):
                self._open_repository()
            return

        if self.state is not GameState.PLAYING:
            self._handle_result_click(position)
            return

        if self.restart_button.contains(position):
            self._open_dialog("restart")
            return

        if self.exit_button.contains(position):
            self._open_dialog("exit")
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

    def _open_dialog(self, action: str) -> None:
        self.dialog_action = action
        self.hover_target = None

    def _open_repository(self) -> None:
        webbrowser.open(REPOSITORY_URL)

    def _handle_dialog_click(self, position: tuple[int, int]) -> None:
        """处理确认框关闭、取消和确认操作。"""
        if (
            self.dialog_close_rect.collidepoint(position)
            or self.dialog_cancel_rect.collidepoint(position)
        ):
            self.dialog_action = None
            self.hover_target = None
            return

        if not self.dialog_confirm_rect.collidepoint(position):
            return

        action = self.dialog_action
        self.dialog_action = None
        self.hover_target = None
        if action == "restart":
            self.restart_level()
        elif action == "exit":
            self.running = False

    def _hover_target_at(self, position: tuple[int, int]) -> str | None:
        """返回鼠标当前悬停的可交互控件标识。"""
        if self.dialog_action is not None:
            if self.dialog_close_rect.collidepoint(position):
                return "dialog_close"
            if self.dialog_confirm_rect.collidepoint(position):
                return "dialog_confirm"
            if self.dialog_cancel_rect.collidepoint(position):
                return "dialog_cancel"
            return None

        if self.state is GameState.START:
            if self.start_button.contains(position):
                return "start"
            if self.custom_mode_button.contains(position):
                return "custom_mode"
            if self.author_link_rect.collidepoint(position):
                return "author"
            return None

        if self.state is GameState.PLAYING:
            if self.restart_button.contains(position):
                return "restart"
            if self.exit_button.contains(position):
                return "exit"
            for tool, rect in self.tool_rects.items():
                if not self.tools.is_used(tool) and rect.collidepoint(position):
                    return f"tool:{tool.value}"
            return None

        if self.result_primary_button.contains(position):
            return "result_primary"
        if self.result_secondary_button.contains(position):
            return "result_secondary"
        return None

    def _update_hover_audio(self, position: tuple[int, int]) -> None:
        """鼠标进入按钮时播放一次 click 音效。"""
        target = self._hover_target_at(position)
        if target is not None and target != self.hover_target:
            self.audio.play("click", volume=0.35)
        self.hover_target = target

    def update(self, delta_time: float) -> None:
        """更新鼠标悬停、提示和短暂碰撞反馈。"""
        mouse_position = pygame.mouse.get_pos()
        self._update_hover_audio(mouse_position)
        if self.dialog_action is not None:
            self.hovered_cell = None
            return

        if self.state is GameState.PLAYING:
            self.hovered_cell = self._cell_at(mouse_position)
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
            next_state = self.pending_result
            self.state = next_state
            self.pending_result = None
            if next_state is GameState.LOSE:
                self.audio.play("fail", volume=0.72)

    def start_game(self) -> None:
        """从第一关开始游戏。"""
        self.current_level_index = 0
        self.audio.play_music("bgm")
        self._load_level(reset_tools=True, reset_mistakes=True)

    def next_level(self) -> None:
        """进入下一关。"""
        if self.current_level_index + 1 < len(LEVELS):
            self.current_level_index += 1
            self.audio.play_music("bgm")
            self._load_level()

    def return_to_start(self) -> None:
        """返回开始界面。"""
        self.state = GameState.START
        self.dialog_action = None
        self.round_finished = False
        self.pending_result = None
        self.hovered_cell = None
        self.effects.reset()

    def restart_level(self) -> None:
        """重新开始整局游戏，并回到第一关。"""
        self.current_level_index = 0
        self.audio.play_music("bgm")
        self._load_level(reset_tools=True, reset_mistakes=True)

    def _load_level(
        self,
        *,
        reset_tools: bool = False,
        reset_mistakes: bool = False,
    ) -> None:
        self.board = copy.deepcopy(LEVELS[self.current_level_index])
        self.dialog_action = None
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
        self.audio.play("miss", volume=0.68)

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

    def _use_remove(self) -> None:
        self.tools.begin_selection(ToolId.REMOVE)
        self.message = "请点击要移出的箭头"

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
            if self.dialog_action is not None:
                self._draw_dialog()
        else:
            self._draw_result_screen()

        pygame.display.flip()

    def _draw_start_screen(self) -> None:
        """绘制偏印刷海报风格的开始界面。"""
        self.screen.blit(self.game_background, (0, 0))

        pygame.draw.line(self.screen, ACCENT, (84, 82), (84, 544), 3)
        pygame.draw.circle(self.screen, ACCENT, (84, 82), 5)

        logo = get_cropped_scaled_ui_asset(START_LOGO_FILE, (390, 190))
        if logo is not None:
            logo_rect = logo.get_rect(topleft=(105, 55))
            self.screen.blit(logo, logo_rect)
        else:
            title = self.title_font.render("Arr0w-voyage", True, INK)
            subtitle = self.start_subtitle_font.render("一箭又一箭", True, ACCENT)
            self.screen.blit(title, (116, 68))
            self.screen.blit(subtitle, (120, 160))

        line = self.body_font.render(
            "观察箭头方向，找到一条通向棋盘外的路。", True, INK_SOFT
        )
        self.screen.blit(line, (120, 280))

        tips = (
            "01  找出前方没有阻挡的箭头",
            "02  规划顺序，避免无路可走",
            "03  清空棋盘，进入下一关",
        )
        for index, tip in enumerate(tips):
            text = self.small_font.render(tip, True, INK)
            self.screen.blit(text, (120, 324 + index * 36))

        mouse_position = pygame.mouse.get_pos()
        self.start_button.draw(self.screen, self.button_font, mouse_position)
        self.custom_mode_button.draw(
            self.screen,
            self.button_font,
            mouse_position,
        )

        self._draw_sample_board()
        self._draw_author_link()
        self._draw_health_notice()

    def _draw_author_link(self) -> None:
        """绘制右下角作者名和 GitHub 仓库入口。"""
        mouse_position = pygame.mouse.get_pos()
        hovered = self.author_link_rect.collidepoint(mouse_position)
        label = self.small_font.render(AUTHOR_NAME, True, INK)
        icon_size = 36
        content_width = label.get_width() + 8 + icon_size
        content_left = self.author_link_rect.right - 12 - content_width

        icon_center = (
            content_left + icon_size // 2,
            self.author_link_rect.centery,
        )
        icon = get_cropped_scaled_ui_asset(GITHUB_ICON_FILE, (icon_size, icon_size))
        if icon is not None:
            icon_rect = icon.get_rect(center=icon_center)
            self.screen.blit(icon, icon_rect)
        else:
            draw_github_icon(self.screen, icon_center, icon_size)

        label_rect = label.get_rect(
            midleft=(icon_center[0] + icon_size // 2 + 8, self.author_link_rect.centery)
        )
        self.screen.blit(label, label_rect)

        if hovered:
            underline_y = self.author_link_rect.bottom - 4
            pygame.draw.line(
                self.screen,
                INK_SOFT,
                (content_left, underline_y),
                (self.author_link_rect.right - 12, underline_y),
                1,
            )

    def _draw_health_notice(self) -> None:
        """绘制开始界面底部的健康游戏忠告。"""
        title = self.small_font.render("健康游戏忠告", True, INK_SOFT)
        title_rect = title.get_rect(center=(650, 498))
        self.screen.blit(title, title_rect)

        lines = (
            "抵制不良游戏，拒绝盗版游戏。注意自我保护，谨防受骗上当。",
            "适度游戏益脑，沉迷游戏伤身。合理安排时间，享受健康生活。",
        )
        for index, line in enumerate(lines):
            text = self.tiny_font.render(line, True, INK_SOFT)
            text_rect = text.get_rect(
                center=(650, 524 + index * 22)
            )
            self.screen.blit(text, text_rect)

    def _draw_sample_board(self) -> None:
        """使用与游戏棋盘一致的素材绘制开始界面棋盘。"""
        board = pygame.Rect(574, 168, 288, 288)
        pygame.draw.rect(
            self.screen,
            PAPER_DEEP,
            board.move(3, 5),
            border_radius=18,
        )
        pygame.draw.rect(self.screen, CELL_BED, board, border_radius=18)

        cell_size = 96
        for row in range(3):
            for col in range(3):
                cell = pygame.Rect(
                    board.left + col * cell_size,
                    board.top + row * cell_size,
                    cell_size,
                    cell_size,
                )
                inner_rect = cell.inflate(-8, -8)
                if not draw_cell_texture(self.screen, inner_rect):
                    pygame.draw.rect(
                        self.screen,
                        CELL_FACE,
                        inner_rect,
                        border_radius=7,
                    )
                pygame.draw.rect(
                    self.screen,
                    CELL_BORDER,
                    inner_rect,
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

        pygame.draw.rect(
            self.screen,
            BOARD_BORDER,
            board,
            width=2,
            border_radius=18,
        )
    def _draw_game_screen(self) -> None:
        """绘制游戏 HUD、棋盘与侧边信息。"""
        self.screen.blit(self.game_background, (0, 0))

        logo = get_cropped_scaled_ui_asset(GAME_LOGO_FILE, (220, 48))
        if logo is not None:
            self.screen.blit(logo, (58, 38))
        else:
            brand = self.heading_font.render("Arr0w-voyage", True, INK)
            self.screen.blit(brand, (58, 38))

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

    def _draw_dialog(self) -> None:
        """绘制重新开始或退出游戏确认框。"""
        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((42, 28, 17, 150))
        self.screen.blit(overlay, (0, 0))

        panel = get_scaled_background_asset(
            DIALOG_PANEL_ASSET,
            self.dialog_panel_rect.size,
        )
        if panel is not None:
            self.screen.blit(panel, self.dialog_panel_rect.topleft)
        else:
            pygame.draw.rect(
                self.screen,
                PAPER_LIGHT,
                self.dialog_panel_rect,
                border_radius=14,
            )

        header = get_scaled_background_asset(
            DIALOG_HEADER_ASSET,
            self.dialog_header_rect.size,
        )
        if header is not None:
            self.screen.blit(header, self.dialog_header_rect.topleft)

        if self.dialog_action == "restart":
            title = "重新开始"
            message_lines = (
                "确定要重新开始吗？",
                "当前进度、失误次数和道具都会重置。",
            )
        else:
            title = "退出游戏"
            message_lines = (
                "确定要退出游戏吗？",
                "未完成的关卡进度将不会保存。",
            )

        title_text = self.heading_font.render(title, True, PAPER_LIGHT)
        title_rect = title_text.get_rect(center=self.dialog_header_rect.center)
        self.screen.blit(title_text, title_rect)

        for index, line in enumerate(message_lines):
            color = INK if index == 0 else INK_SOFT
            font = self.body_font if index == 0 else self.small_font
            text = font.render(line, True, color)
            text_rect = text.get_rect(
                center=(self.dialog_panel_rect.centerx, 296 + index * 36)
            )
            self.screen.blit(text, text_rect)

        mouse_position = pygame.mouse.get_pos()
        for rect, label in (
            (self.dialog_confirm_rect, "确认"),
            (self.dialog_cancel_rect, "取消"),
        ):
            button = get_scaled_background_asset(
                DIALOG_BUTTON_ASSET,
                rect.size,
            )
            if button is not None:
                self.screen.blit(button, rect.topleft)
            else:
                pygame.draw.rect(self.screen, ACCENT, rect, border_radius=8)

            if rect.collidepoint(mouse_position):
                pygame.draw.rect(
                    self.screen,
                    PAPER_LIGHT,
                    rect,
                    width=2,
                    border_radius=8,
                )

            label_text = self.small_button_font.render(
                label, True, PAPER_LIGHT
            )
            label_rect = label_text.get_rect(center=rect.center)
            self.screen.blit(label_text, label_rect)

        close_image = get_scaled_background_asset(
            DIALOG_CLOSE_ASSET,
            self.dialog_close_rect.size,
        )
        if close_image is not None:
            self.screen.blit(close_image, self.dialog_close_rect.topleft)

    def _draw_result_screen(self) -> None:
        """绘制关卡完成、全部通关和失败结果界面。"""
        self.screen.blit(self.game_background, (0, 0))

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

        logo = get_cropped_scaled_ui_asset(GAME_LOGO_FILE, (220, 48))
        if logo is not None:
            self.screen.blit(logo, (128, 88))
        else:
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
                use_cell_texture = True

                if direction is not None and self.hovered_cell == (row, col):
                    fill_color = PAPER_HOVER
                    border_color = CELL_HOVER_BORDER
                    use_cell_texture = False

                if direction is not None and self.tools.pending is ToolId.REMOVE:
                    fill_color = CELL_HINT
                    border_color = MOSS
                    use_cell_texture = False

                if direction is not None and self.effects.hint_cell == (row, col):
                    fill_color = CELL_HINT
                    border_color = MOSS
                    border_width = 2
                    use_cell_texture = False

                if self.effects.feedback_cell == (row, col):
                    fill_color = CELL_BLOCKED
                    border_color = ACCENT
                    border_width = 2
                    use_cell_texture = False

                if not use_cell_texture or not draw_cell_texture(
                    self.screen, inner_rect
                ):
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
            description_color = (255, 255, 255)
        else:
            fill_color = PAPER_HOVER if hovered else CELL_FACE
            border_color = CELL_HOVER_BORDER if hovered else RULE
            icon_color = MOSS
            description_color = (255, 255, 255)

        frame = get_scaled_background_asset(
            TOOL_FRAME_ASSET,
            rect.size,
            rotate=90,
        )
        if frame is not None:
            self.screen.blit(frame, rect.topleft)
            if used:
                disabled_overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                disabled_overlay.fill((210, 205, 195, 145))
                self.screen.blit(disabled_overlay, rect.topleft)
            elif hovered:
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    rect,
                    width=2,
                    border_radius=10,
                )
        else:
            pygame.draw.rect(self.screen, fill_color, rect, border_radius=10)
            pygame.draw.rect(
                self.screen,
                border_color,
                rect,
                width=1,
                border_radius=10,
            )

        icon_center = (rect.left + 38, rect.centery)
        draw_tool_icon(self.screen, tool.value, icon_center, icon_color)

        description = self.body_font.render(
            TOOL_DESCRIPTIONS[tool], True, description_color
        )
        description_rect = description.get_rect(
            midleft=(rect.left + 62, rect.centery)
        )
        self.screen.blit(description, description_rect)

        status_text = f"X{self.tools.remaining[tool]}"
        status = self.tiny_font.render(status_text, True, description_color)
        status_rect = status.get_rect(
            midright=(rect.right - 28, rect.centery)
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
