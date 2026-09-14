"""道具状态测试。"""

from tools import TOOL_KEYS, ToolId, ToolState


def test_tools_start_with_one_use() -> None:
    state = ToolState()
    assert all(state.remaining[tool] == 1 for tool in TOOL_KEYS)


def test_consuming_tool_marks_it_used() -> None:
    state = ToolState()
    assert state.consume(ToolId.HINT) is True
    assert state.remaining[ToolId.HINT] == 0
    assert state.is_used(ToolId.HINT) is True
    assert state.consume(ToolId.HINT) is False


def test_reset_restores_tools_and_clears_selection() -> None:
    state = ToolState()
    state.consume(ToolId.REMOVE)
    state.begin_selection(ToolId.REMOVE)
    state.reset()
    assert state.remaining[ToolId.REMOVE] == 1
    assert state.pending is None


def test_remove_tool_supports_target_selection() -> None:
    state = ToolState()
    state.begin_selection(ToolId.REMOVE)
    assert state.pending is ToolId.REMOVE
    state.cancel_selection()
    assert state.pending is None
