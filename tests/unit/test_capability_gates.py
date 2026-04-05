"""Unit tests for brewer capability gate evaluation."""

from beanbay.services.parameter_ranges import evaluate_requires


class FakeBrewer:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_none_requires_always_passes():
    assert evaluate_requires(None, FakeBrewer()) is True


def test_not_equal_none():
    brewer = FakeBrewer(preinfusion_type="timed")
    assert evaluate_requires("preinfusion_type != none", brewer) is True


def test_not_equal_none_fails():
    brewer = FakeBrewer(preinfusion_type="none")
    assert evaluate_requires("preinfusion_type != none", brewer) is False


def test_in_list():
    brewer = FakeBrewer(pressure_control_type="electronic")
    assert (
        evaluate_requires(
            "pressure_control_type in (opv_adjustable, electronic, programmable)",
            brewer,
        )
        is True
    )


def test_in_list_fails():
    brewer = FakeBrewer(pressure_control_type="fixed")
    assert (
        evaluate_requires(
            "pressure_control_type in (opv_adjustable, electronic, programmable)",
            brewer,
        )
        is False
    )


def test_equals_true():
    brewer = FakeBrewer(has_bloom=True)
    assert evaluate_requires("has_bloom == true", brewer) is True


def test_equals_true_fails():
    brewer = FakeBrewer(has_bloom=False)
    assert evaluate_requires("has_bloom == true", brewer) is False


def test_equals_value():
    brewer = FakeBrewer(flow_control_type="programmable")
    assert evaluate_requires("flow_control_type == programmable", brewer) is True


def test_equals_value_fails():
    brewer = FakeBrewer(flow_control_type="none")
    assert evaluate_requires("flow_control_type == programmable", brewer) is False
