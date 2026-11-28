"""Plain-text summary of an audit run."""

from sales_dq_auditor.models import AuditReport


def format_console(report: AuditReport) -> str:
    """Return the PASS/WARN/FAIL summary as text."""
    lines = ["Check Results", "─" * 55]
    for result in report.results:
        lines.append(f"[{result.status.upper()}]  {result.name}")
        lines.append(f"       {result.message}")
    return "\n".join(lines)