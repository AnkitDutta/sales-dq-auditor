import pytest

from sales_dq_auditor.checks import business
from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.models import Status


@pytest.mark.parametrize("check", business.BUSINESS_CHECKS)
def test_ordinary_data_passes(check, make_df, config):
    result = check(make_df(), config)

    assert result.status == Status.PASS
    assert result.total_flagged == 0


def test_extreme_loss_is_a_failure(make_df, config):
    df = make_df(rows=21, Profit=[10.0] * 20 + [-1000.0])

    result = business.check_extreme_losses(df, config)

    assert result.status == Status.FAIL
    assert result.total_flagged == 1
    assert result.metrics["total_loss"] == 1000.0
    assert result.details["Loss"].tolist() == [1000.0]


def test_extreme_gain_is_a_warning(make_df, config):
    df = make_df(rows=21, Profit=[10.0] * 20 + [1000.0])

    result = business.check_extreme_gains(df, config)

    assert result.status == Status.WARN
    assert result.total_flagged == 1


@pytest.mark.parametrize(("discount", "flagged"), [(0.5, 0), (0.51, 1)])
def test_high_discount_boundary(discount, flagged, make_df, config):
    result = business.check_high_discount(make_df(rows=1, Discount=discount), config)

    assert result.total_flagged == flagged


def test_profit_is_never_shown_as_loss(make_df, config):
    df = make_df(rows=2, Discount=0.6, Profit=[20.0, -30.0])

    result = business.check_high_discount(df, config)

    assert result.details["Loss"].tolist() == [0.0, 30.0]
    assert result.metrics["total_loss"] == 30.0


def test_discount_driven_loss_needs_both_conditions(make_df, config):
    df = make_df(rows=3, Discount=[0.6, 0.6, 0.1], Profit=[-5.0, 5.0, -5.0])

    result = business.check_discount_driven_losses(df, config)

    assert result.details["Order ID"].tolist() == ["ORD-0"]


def test_unexplained_loss_boundaries(make_df, config):
    df = make_df(rows=3, Discount=[0.2, 0.2, 0.21], Profit=[-500.0, -501.0, -501.0])

    result = business.check_unexplained_losses(df, config)

    assert result.details["Order ID"].tolist() == ["ORD-1"]


@pytest.mark.parametrize("flagged", [1, 3, 10])
def test_no_note_row_is_added(flagged, make_df, config):
    df = make_df(rows=flagged, Discount=0.8, Profit=-5.0)

    result = business.check_high_discount(df, config)

    assert len(result.details) == flagged
    assert result.total_flagged == flagged


def test_thresholds_come_from_config(make_df):
    config = AuditConfig(high_discount=0.4)

    result = business.check_high_discount(make_df(rows=1, Discount=0.45), config)

    assert result.name == "High Discount Orders (>40%)"
    assert result.total_flagged == 1
