"""Shared fixtures: small, hand-made sales tables."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from sales_dq_auditor.config import AuditConfig


@pytest.fixture
def config() -> AuditConfig:
    return AuditConfig()


@pytest.fixture
def make_df() -> Callable[..., pd.DataFrame]:
    """Build a clean table. Pass a list or a single value to override a column."""

    def _make(rows: int = 3, **overrides: Any) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "Order ID": [f"ORD-{number}" for number in range(rows)],
                "Order Date": [pd.Timestamp("2017-01-10")] * rows,
                "Ship Date": [pd.Timestamp("2017-01-12")] * rows,
                "Product Name": [f"Product {number}" for number in range(rows)],
                "Category": ["Technology"] * rows,
                "Sales": [100.0] * rows,
                "Quantity": [2] * rows,
                "Discount": [0.0] * rows,
                "Profit": [10.0] * rows,
            }
        )
        for column, value in overrides.items():
            df[column.replace("_", " ")] = value
        return df

    return _make


@pytest.fixture
def write_csv(tmp_path: Path) -> Callable[..., Path]:
    """Save a table as a CSV laid out like the real input file."""

    def _write(df: pd.DataFrame) -> Path:
        path = tmp_path / "sales.csv"
        df.to_csv(path, index=False, encoding="latin-1", date_format="%m/%d/%Y")
        return path

    return _write
