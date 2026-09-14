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


def test_flying_arrow_progresses_and_expires() -> None:
    state = AnimationState()
    state.start_fly((1, 2), "RIGHT", duration=0.4)

    assert len(state.flying_arrows) == 1
    assert state.flying_arrows[0].progress == 0.0

    state.update(0.2)
    assert 0.0 < state.flying_arrows[0].progress < 1.0

    state.update(0.2)
    assert state.flying_arrows == []


def test_multiple_flying_arrows_are_tracked_independently() -> None:
    state = AnimationState()
    state.start_fly((0, 0), "RIGHT", duration=0.2)
    state.start_fly((1, 1), "DOWN", duration=0.5)

    state.update(0.2)
    assert len(state.flying_arrows) == 1
    assert state.flying_arrows[0].direction == "DOWN"


def test_reset_clears_all_effect_state() -> None:
    state = AnimationState()
    state.show_feedback((0, 0))
    state.show_hint((1, 1))
    state.show_toast("测试")
    state.start_fly((0, 0), "UP")
    state.reset()
    assert state == AnimationState()
