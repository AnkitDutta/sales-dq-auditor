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


@dataclass(frozen=True)
class AuditReport:
    """The results of one audit run, plus facts about the input file."""

    results: tuple[CheckResult, ...]
    source_name: str
    row_count: int
    column_count: int
    first_year: int
    last_year: int

    def count(self, status: Status) -> int:
        """Count the checks that ended with the given status."""
        return sum(result.status == status for result in self.results)

    @property
    def score(self) -> int:
        """Percentage of checks that passed. Warnings don't count as passes."""
        if not self.results:
            return 0
        return round(self.count(Status.PASS) / len(self.results) * 100)