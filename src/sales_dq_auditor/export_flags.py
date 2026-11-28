"""Export every sales row with True/False flag columns for the Power BI dashboard."""

from pathlib import Path

import pandas as pd

from sales_dq_auditor.checks import business
from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.loader import load_sales_data

FLAG_CHECKS = {
    "flag_extreme_loss": business.check_extreme_losses,
    "flag_extreme_gain": business.check_extreme_gains,
    "flag_high_discount": business.check_high_discount,
    "flag_discount_loss": business.check_discount_driven_losses,
    "flag_unexplained_loss": business.check_unexplained_losses,
}
OUTPUT_NAME = "superstore_flagged.csv"


def add_flags(df: pd.DataFrame, config: AuditConfig) -> pd.DataFrame:
    """Return a copy of the data with one flag column per business check."""
    flagged = df.copy()
    for column, check in FLAG_CHECKS.items():
        flagged[column] = df.index.isin(check(df, config).details.index)
    flagged["flag_count"] = flagged[list(FLAG_CHECKS)].sum(axis=1)
    return flagged


def export_flags(config: AuditConfig) -> Path:
    """Load the data, add the flags and save them as a CSV."""
    flagged = add_flags(load_sales_data(config.input_path), config)
    output_path = config.output_path.parent / OUTPUT_NAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    flagged.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    config = AuditConfig()
    output_path = export_flags(config)
    flags = pd.read_csv(output_path, usecols=list(FLAG_CHECKS))
    print(flags.sum())
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
