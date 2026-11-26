"""Core data types shared across the auditor."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import pandas as pd


class Status(StrEnum):
    """Outcome of a single check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class Category(StrEnum):
    """Which family a check belongs to."""

    QUALITY = "quality"
    BUSINESS = "business"


@dataclass(frozen=True)
class CheckResult:
    """Everything a check reports back."""

    name: str
    category: Category
    status: Status
    message: str
    details: pd.DataFrame = field(default_factory=pd.DataFrame)
    total_flagged: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)