"""动画和提示状态测试。"""

from animations import AnimationState


def test_feedback_expires_after_update() -> None:
    state = AnimationState()
    state.show_feedback((1, 2), duration=0.2)
    state.update(0.1)
    assert state.feedback_cell == (1, 2)
    state.update(0.1)
    assert state.feedback_cell is None


def test_hint_and_toast_expire_independently() -> None:
    state = AnimationState()
    state.show_hint((0, 1), duration=1.0)
    state.show_toast("提示", duration=0.5)
    state.update(0.5)
    assert state.hint_cell == (0, 1)
    assert state.toast_text is None


def test_reset_clears_all_effect_state() -> None:
    state = AnimationState()
    state.show_feedback((0, 0))
    state.show_hint((1, 1))
    state.show_toast("测试")
    state.reset()
    assert state == AnimationState()
