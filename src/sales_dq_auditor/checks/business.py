"""Business rule checks: is something worrying going on in the sales?"""

from typing import Any

import pandas as pd

from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.models import Category, CheckResult, Status

DETAIL_COLUMNS = ["Order ID", "Product Name", "Category", "Sales", "Discount", "Profit"]


def _result(
    name: str,
    status_if_flagged: Status,
    details: pd.DataFrame,
    pass_message: str,
    flagged_message: str,
    metrics: dict[str, Any] | None = None,
) -> CheckResult:
    """Build a pass result, or a flagged result when there are rows to report."""
    if details.empty:
        return CheckResult(name, Category.BUSINESS, Status.PASS, pass_message)
    return CheckResult(
        name,
        Category.BUSINESS,
        status_if_flagged,
        flagged_message,
        details=details,
        total_flagged=len(details),
        metrics=metrics or {},
    )


def _profit_limits(df: pd.DataFrame, sigma: float) -> tuple[float, float]:
    """Return the lower and upper limits for a normal Profit value."""
    mean = df["Profit"].mean()
    spread = sigma * df["Profit"].std()
    return mean - spread, mean + spread


def _total_loss(rows: pd.DataFrame) -> float:
    """Add up the money lost on loss-making rows, as a positive number."""
    return float(abs(rows.loc[rows["Profit"] < 0, "Profit"].sum()))


def _with_loss_column(rows: pd.DataFrame) -> pd.DataFrame:
    """Swap Profit for a Loss column. Profitable rows get a Loss of 0."""
    result = rows.copy()
    result["Loss"] = (-result["Profit"]).clip(lower=0).round(4)
    return result.drop(columns=["Profit"])


def check_extreme_losses(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    lower, _ = _profit_limits(df, config.sigma)
    bad = df.loc[df["Profit"] < lower, DETAIL_COLUMNS]
    total_loss = _total_loss(bad)
    return _result(
        "Extreme Loss Outliers",
        Status.FAIL,
        _with_loss_column(bad),
        "No extreme loss outliers detected.",
        f"{len(bad):,} order(s) with losses beyond {config.sigma:g} standard deviations "
        f"from mean profit. Total loss: ${total_loss:,.2f}.",
        {"total_loss": total_loss},
    )


def check_extreme_gains(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    _, upper = _profit_limits(df, config.sigma)
    flagged = df.loc[df["Profit"] > upper, DETAIL_COLUMNS]
    return _result(
        "Extreme Profit Outliers",
        Status.WARN,
        flagged,
        "No unusually high profit outliers detected.",
        f"{len(flagged):,} order(s) with profit beyond {config.sigma:g} standard deviations "
        "above mean — validate these are not data entry errors.",
    )


def check_high_discount(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    columns = ["Order ID", "Product Name", "Discount", "Profit"]
    bad = df.loc[df["Discount"] > config.high_discount, columns]
    total_loss = _total_loss(bad)
    limit = f"{config.high_discount:.0%}"
    return _result(
        f"High Discount Orders (>{limit})",
        Status.WARN,
        _with_loss_column(bad),
        f"No discounts above {limit} found.",
        f"{len(bad):,} order(s) with Discount above {limit}. "
        f"Those with negative profit represent ${total_loss:,.2f} in losses.",
        {"total_loss": total_loss},
    )


def check_discount_driven_losses(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    flagged = (df["Discount"] > config.high_discount) & (df["Profit"] < 0)
    bad = df.loc[flagged, DETAIL_COLUMNS]
    total_loss = _total_loss(bad)
    return _result(
        "Discount-Driven Losses",
        Status.WARN,
        _with_loss_column(bad),
        "No high-discount orders with negative profit found.",
        f"{len(bad):,} order(s) with Discount >{config.high_discount:.0%} and negative Profit. "
        f"Discount policy is directly driving ${total_loss:,.2f} in losses.",
        {"total_loss": total_loss},
    )


def check_unexplained_losses(df: pd.DataFrame, config: AuditConfig) -> CheckResult:
    flagged = (df["Profit"] < config.unexplained_loss) & (df["Discount"] <= config.low_discount)
    bad = df.loc[flagged, DETAIL_COLUMNS]
    total_loss = _total_loss(bad)
    return _result(
        "Unexplained Losses",
        Status.WARN,
        _with_loss_column(bad),
        "No significant losses found outside of discount policy.",
        f"{len(bad):,} order(s) with Loss above ${abs(config.unexplained_loss):,.0f} "
        f"at ≤{config.low_discount:.0%} discount — losses not explained by discounting alone. "
        f"Total: ${total_loss:,.2f}. Possible cost basis or pricing issue.",
        {"total_loss": total_loss},
    )


BUSINESS_CHECKS = (
    check_extreme_losses,
    check_extreme_gains,
    check_high_discount,
    check_discount_driven_losses,
    check_unexplained_losses,
)
