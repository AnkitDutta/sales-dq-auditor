"""Allow `python -m sales_dq_auditor`."""

import sys

from sales_dq_auditor.cli import main

sys.exit(main())