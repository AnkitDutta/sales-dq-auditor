import runpy
import sys

import pytest

from sales_dq_auditor.cli import main


def test_writes_report_to_the_chosen_path(make_df, write_csv, tmp_path, capsys):
    output = tmp_path / "nested" / "report.html"

    code = main(["--input", str(write_csv(make_df())), "--output", str(output)])

    assert code == 0
    assert "Data Quality Report" in output.read_text(encoding="utf-8")
    assert "[PASS]  Missing Values" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("overrides", "fail_on", "expected"),
    [
        ({"Sales": -1.0}, "never", 0),
        ({"Sales": -1.0}, "fail", 1),
        ({"Sales": -1.0}, "warn", 1),
        ({"Discount": 0.8}, "fail", 0),
        ({"Discount": 0.8}, "warn", 1),
        ({}, "warn", 0),
    ],
)
def test_fail_on_controls_exit_code(overrides, fail_on, expected, make_df, write_csv, tmp_path):
    path = write_csv(make_df(rows=1, **overrides))
    args = ["--input", str(path), "--output", str(tmp_path / "r.html"), "--fail-on", fail_on]

    assert main(args) == expected


def test_missing_input_returns_error(tmp_path, caplog):
    code = main(["--input", str(tmp_path / "nope.csv")])

    assert code == 2
    assert "nope.csv" in caplog.text


def test_python_dash_m_runs_the_cli(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dq-audit", "--version"])

    with pytest.raises(SystemExit) as stop:
        runpy.run_module("sales_dq_auditor", run_name="__main__")

    assert stop.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
