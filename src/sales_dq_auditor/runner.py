"""Run every check and collect the results."""

import pandas as pd

from sales_dq_auditor.checks import ALL_CHECKS
from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.models import AuditReport


def run_checks(df: pd.DataFrame, config: AuditConfig) -> AuditReport:
    """Run all checks on the data and return a report."""
    return AuditReport(
        results=tuple(check(df, config) for check in ALL_CHECKS),
        source_name=config.input_path.name,
        row_count=len(df),
        column_count=len(df.columns),
        first_year=int(df["Order Date"].min().year),
        last_year=int(df["Ship Date"].max().year),
    )
