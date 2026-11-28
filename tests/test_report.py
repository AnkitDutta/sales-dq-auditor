from datetime import datetime

import pytest

from sales_dq_auditor.report.console import format_console
from sales_dq_auditor.report.html import _score_color, render_html
from sales_dq_auditor.runner import run_checks

NOW = datetime(2026, 1, 2, 3, 4)


def render(df, config):
    return render_html(run_checks(df, config), config.sample_size, NOW)


def test_report_lists_every_check_and_fills_the_template(make_df, config):
    html = render(make_df(), config)

    assert html.count('class="check-row"') == 11
    assert "02 Jan 2026, 03:04" in html
    assert "<span>9</span>" in html
    assert "2017 – 2017" in html
    assert "$" not in html


def test_product_names_are_escaped(make_df, config):
    df = make_df(rows=1, Product_Name="<script>x</script>", Discount=0.8)

    html = render(df, config)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize(("rows", "has_note"), [(10, False), (11, True)])
def test_truncation_note_only_when_rows_are_hidden(rows, has_note, make_df, config):
    html = render(make_df(rows=rows, Discount=0.8), config)

    assert (f"Showing 10 of {rows} rows" in html) is has_note


@pytest.mark.parametrize(
    ("score", "color"),
    [(80, "#065f46"), (79, "#92400e"), (60, "#92400e"), (59, "#991b1b")],
)
def test_score_color_boundaries(score, color):
    assert _score_color(score) == color


def test_console_shows_status_and_message(make_df, config):
    text = format_console(run_checks(make_df(), config))

    assert "[PASS]  Missing Values" in text
    assert "No missing values across all 9 columns." in text
