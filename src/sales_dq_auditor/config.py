"""Settings for an audit run."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditConfig:
    """Thresholds, sample size and file paths used by the auditor script"""

    # Business rule thresholds
    high_discount: float = 0.5
    low_discount: float = 0.2
    unexplained_loss: float = -500.0
    sigma: float = 3.0

    # Report
    sample_size: int = 10

    # Files
    input_path: Path = Path("data/superstore.csv")
    output_path: Path = Path("output/dq_report.html")
