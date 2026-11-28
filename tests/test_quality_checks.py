import pandas as pd
import pytest

from sales_dq_auditor.checks import quality
from sales_dq_auditor.models import Status


@pytest.mark.parametrize("check", quality.QUALITY_CHECKS)
def test_clean_data_passes(check, make_df, config):
    result = check(make_df(), config)

    assert result.status == Status.PASS
    assert result.total_flagged == 0
    assert result.details.empty


def test_nulls_are_counted_per_column(make_df, config):
    df = make_df(rows=4, Category=[None, None, "a", "b"], Sales=[None, 1.0, 1.0, 1.0])

    result = quality.check_nulls(df, config)

    assert result.status == Status.FAIL
    assert result.total_flagged == 2
    percentages = dict(zip(result.details["Column"], result.details["% of Rows"], strict=True))
    assert percentages == {"Category": 50.0, "Sales": 25.0}


def test_exact_duplicate_is_flagged(make_df, config):
    df = make_df()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    result = quality.check_duplicates(df, config)

    assert result.status == Status.FAIL
    assert result.total_flagged == 1


@pytest.mark.parametrize(("value", "flagged"), [(-1.0, 1), (0.0, 1), (0.01, 0)])
def test_sales_boundary(value, flagged, make_df, config):
    result = quality.check_negative_sales(make_df(rows=1, Sales=value), config)

    assert result.total_flagged == flagged


@pytest.mark.parametrize(("value", "flagged"), [(-1, 1), (0, 1), (1, 0)])
def test_quantity_boundary(value, flagged, make_df, config):
    result = quality.check_negative_quantity(make_df(rows=1, Quantity=value), config)

    assert result.total_flagged == flagged


@pytest.mark.parametrize(("value", "flagged"), [(-0.1, 1), (0.0, 0), (1.0, 0), (1.1, 1)])
def test_discount_range_boundary(value, flagged, make_df, config):
    result = quality.check_discount_range(make_df(rows=1, Discount=value), config)

    assert result.total_flagged == flagged


@pytest.mark.parametrize(("ship_date", "flagged"), [("2017-01-09", 1), ("2017-01-10", 0)])
def test_ship_date_boundary(ship_date, flagged, make_df, config):
    df = make_df(rows=1, Ship_Date=pd.Timestamp(ship_date))

    result = quality.check_ship_before_order(df, config)

    assert result.total_flagged == flagged
