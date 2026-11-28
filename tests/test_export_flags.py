import pandas as pd

from sales_dq_auditor import export_flags
from sales_dq_auditor.config import AuditConfig


def test_flags_mark_the_right_rows(make_df, config):
    df = make_df(rows=2, Discount=[0.8, 0.0], Profit=[-5.0, 10.0])

    flagged = export_flags.add_flags(df, config)

    assert flagged["flag_high_discount"].tolist() == [True, False]
    assert flagged["flag_discount_loss"].tolist() == [True, False]
    assert flagged["flag_count"].tolist() == [2, 0]
    assert "flag_count" not in df.columns


def test_main_writes_the_csv(make_df, write_csv, tmp_path, monkeypatch, capsys):
    config = AuditConfig(input_path=write_csv(make_df()), output_path=tmp_path / "out" / "r.html")
    monkeypatch.setattr(export_flags, "AuditConfig", lambda: config)

    export_flags.main()

    saved = pd.read_csv(tmp_path / "out" / export_flags.OUTPUT_NAME)
    assert len(saved) == 3
    assert "Saved" in capsys.readouterr().out
