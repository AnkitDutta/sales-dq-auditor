"""Regression test: the real data must give the same results as the original script."""

from pathlib import Path

import pytest

from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.export_flags import FLAG_CHECKS, add_flags
from sales_dq_auditor.loader import load_sales_data
from sales_dq_auditor.report.console import format_console
from sales_dq_auditor.runner import run_checks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real_config():
    return AuditConfig(input_path=ROOT / "data" / "superstore.csv")


@pytest.fixture(scope="module")
def real_df(real_config):
    return load_sales_data(real_config.input_path)


def test_results_match_the_original_script(real_df, real_config):
    report = run_checks(real_df, real_config)
    baseline = (ROOT / "baseline" / "console_before.txt").read_text(encoding="utf-8")

    assert format_console(report) in baseline
    assert [r.total_flagged for r in report.results] == [0, 0, 0, 0, 0, 0, 37, 70, 856, 856, 2]
    assert report.score == 55


def test_dashboard_flag_totals(real_df, real_config):
    flagged = add_flags(real_df, real_config)

    assert flagged[list(FLAG_CHECKS)].sum().tolist() == [37, 70, 856, 856, 2]
