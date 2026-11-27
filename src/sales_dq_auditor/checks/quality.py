"""Data quality checks: is the data itself broken?"""

import pandas as pd

from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.models import Category, CheckResult, Status

def _row_result(name: str, bad: pd.DataFrame, pass_message: str, fail_message: str) -> CheckResult:
    """Build the result for a check where any flagged row is a failure."""
    if bad.empty:
        return CheckResult(name, Category.QUALITY, Status.PASS, pass_message)
    return CheckResult(
        name, Category.QUALITY, Status.FAIL, fail_message, details=bad, total_flagged=len(bad)
    )
    
def check_nulls(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    detail = null_counts.reset_index()
    detail.columns = ["Column", "Null Count"]
    detail["% of Rows"] = (detail["Null Count"] / len(df) * 100).round(2)
    return _row_result(
        "Missing Values",
        detail,
        f"No missing values across all {len(df.columns)} columns.",
        f"{len(detail)} column(s) contain missing values.",
    )


def check_duplicates(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    bad = df[df.duplicated()]
    return _row_result(
        "Duplicate Rows",
        bad,
        "No duplicate rows found.",
        f"{len(bad):,} fully duplicate row(s) detected.",
    )


def check_negative_sales(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    bad = df.loc[df["Sales"] <= 0, ["Order ID", "Product Name", "Category", "Sales"]]
    return _row_result(
        "Negative Sales",
        bad,
        "All Sales values are positive.",
        f"{len(bad):,} row(s) with zero or negative Sales.",
    )


def check_negative_quantity(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    bad = df.loc[df["Quantity"] <= 0, ["Order ID", "Product Name", "Quantity"]]
    return _row_result(
        "Negative Quantity",
        bad,
        "All Quantity values are positive.",
        f"{len(bad):,} row(s) with zero or negative Quantity.",
    )


def check_discount_range(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    outside = (df["Discount"] < 0) | (df["Discount"] > 1)
    bad = df.loc[outside, ["Order ID", "Product Name", "Discount"]]
    return _row_result(
        "Discount Out of Range",
        bad,
        "All Discount values fall within the valid 0–1 range.",
        f"{len(bad):,} row(s) with Discount outside 0–1.",
    )


def check_ship_before_order(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    early = df["Ship Date"] < df["Order Date"]
    bad = df.loc[early, ["Order ID", "Order Date", "Ship Date"]]
    return _row_result(
        "Ship Date Before Order Date",
        bad,
        "No orders found where Ship Date precedes Order Date.",
        f"{len(bad):,} row(s) where Ship Date is before Order Date.",
    )


QUALITY_CHECKS = (
    check_nulls,
    check_duplicates,
    check_negative_sales,
    check_negative_quantity,
    check_discount_range,
    check_ship_before_order,
)