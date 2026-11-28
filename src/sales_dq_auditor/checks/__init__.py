"""Data quality and business rule checks."""

from sales_dq_auditor.checks.business import BUSINESS_CHECKS
from sales_dq_auditor.checks.quality import QUALITY_CHECKS

ALL_CHECKS = QUALITY_CHECKS + BUSINESS_CHECKS