"""Command-line interface for the auditor."""

import argparse
import io
import logging
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from sales_dq_auditor import __version__
from sales_dq_auditor.config import AuditConfig
from sales_dq_auditor.loader import load_sales_data
from sales_dq_auditor.models import AuditReport, Status
from sales_dq_auditor.report.console import format_console
from sales_dq_auditor.report.html import render_html
from sales_dq_auditor.runner import run_checks

EXIT_OK = 0
EXIT_CHECKS_FAILED = 1
EXIT_ERROR = 2

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Describe the command-line options."""
    defaults = AuditConfig()
    parser = argparse.ArgumentParser(prog="dq-audit", description="Audit a sales CSV file.")
    parser.add_argument("--input", type=Path, default=defaults.input_path, help="CSV to audit")
    parser.add_argument(
        "--output", type=Path, default=defaults.output_path, help="HTML report to write"
    )
    parser.add_argument(
        "--fail-on",
        choices=["fail", "warn", "never"],
        default="never",
        help="exit with code 1 on failures, on warnings or failures, or never",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def exit_code(report: AuditReport, fail_on: str) -> int:
    """Decide the exit code from the results and the --fail-on option."""
    if fail_on == "never":
        return EXIT_OK
    blocking = {Status.FAIL, Status.WARN} if fail_on == "warn" else {Status.FAIL}
    if any(result.status in blocking for result in report.results):
        return EXIT_CHECKS_FAILED
    return EXIT_OK


def _use_utf8_output() -> None:
    """Stop redirected output crashing on Windows when it contains non-ASCII text."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run an audit and return the exit code."""
    args = build_parser().parse_args(argv)
    _use_utf8_output()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = AuditConfig(input_path=args.input, output_path=args.output)

    try:
        df = load_sales_data(config.input_path)
        logger.info("Loaded %s rows, %s columns", f"{len(df):,}", len(df.columns))
        report = run_checks(df, config)
        print(format_console(report))
        html = render_html(report, config.sample_size, datetime.now())
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(html, encoding="utf-8")
    except (OSError, ValueError) as err:
        logger.error("%s", err)
        return EXIT_ERROR

    logger.info("Report saved to %s", config.output_path)
    return exit_code(report, args.fail_on)