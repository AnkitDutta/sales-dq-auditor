"""Render an AuditReport as a self-contained HTML page."""

from datetime import datetime
from html import escape
from importlib.resources import files
from string import Template

from sales_dq_auditor.models import AuditReport, CheckResult, Status

BADGES = {
    Status.PASS: ("background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0", "Pass"),
    Status.WARN: ("background:#fffbeb;color:#92400e;border:1px solid #fcd34d", "Warning"),
    Status.FAIL: ("background:#fef2f2;color:#991b1b;border:1px solid #fca5a5", "Fail"),
}
BADGE_BASE = "padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;letter-spacing:0.03em"


def _status_badge(status: Status) -> str:
    style, label = BADGES[status]
    return f'<span style="{style};{BADGE_BASE}">{label}</span>'


def _detail_table(result: CheckResult, sample_size: int) -> str:
    """Show the first few flagged rows, and say so if some are hidden."""
    if result.details.empty:
        return ""
    shown = result.details.head(sample_size)
    note = ""
    if result.total_flagged > len(shown):
        note = f'<p class="table-note">Showing {len(shown)} of {result.total_flagged:,} rows</p>'
    table = shown.to_html(index=False, border=0, classes="detail-table", escape=True)
    return f'<div class="detail-wrap">{note}{table}</div>'


def _check_card(result: CheckResult, sample_size: int) -> str:
    return f"""
        <div class="check-row">
            <div class="check-top">
                <span class="check-name">{escape(result.name)}</span>
                {_status_badge(result.status)}
            </div>
            <p class="check-msg">{escape(result.message)}</p>
            {_detail_table(result, sample_size)}
        </div>
        """


def _score_color(score: int) -> str:
    if score >= 80:
        return "#065f46"
    if score >= 60:
        return "#92400e"
    return "#991b1b"


def render_html(report: AuditReport, sample_size: int, generated_at: datetime) -> str:
    """Fill the HTML template with the results of an audit."""
    template = files("sales_dq_auditor.report").joinpath("template.html")
    return Template(template.read_text(encoding="utf-8")).substitute(
        source_name=escape(report.source_name),
        generated_at=generated_at.strftime("%d %b %Y, %H:%M"),
        score=report.score,
        score_color=_score_color(report.score),
        passed=report.count(Status.PASS),
        warned=report.count(Status.WARN),
        failed=report.count(Status.FAIL),
        row_count=f"{report.row_count:,}",
        column_count=report.column_count,
        check_count=len(report.results),
        years=f"{report.first_year} – {report.last_year}",
        checks_html="".join(_check_card(result, sample_size) for result in report.results),
    )