from sales_dq_auditor.checks import ALL_CHECKS
from sales_dq_auditor.models import AuditReport, Status
from sales_dq_auditor.runner import run_checks


def test_runs_every_check_in_order(make_df, config):
    df = make_df()

    report = run_checks(df, config)

    assert [r.name for r in report.results] == [check(df, config).name for check in ALL_CHECKS]
    assert len(report.results) == 11
    assert report.score == 100


def test_report_facts_come_from_the_data(make_df, config):
    report = run_checks(make_df(), config)

    assert (report.row_count, report.column_count) == (3, 9)
    assert (report.first_year, report.last_year) == (2017, 2017)
    assert report.source_name == "superstore.csv"


def test_warnings_do_not_count_as_passes(make_df, config):
    report = run_checks(make_df(rows=1, Discount=0.8), config)

    assert report.count(Status.WARN) == 1
    assert report.score == 91


def test_empty_report_scores_zero():
    report = AuditReport((), "x.csv", 0, 0, 2017, 2017)

    assert report.score == 0
