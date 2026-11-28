# Sales DQ Auditor — Production Refactor Plan

_Status: draft for review · 2026-11-10_

## 1. What the project does today

**Note:** the repo has **no Jupyter notebooks**. It's a single script, `auditor.py` (≈460 lines), plus `data/superstore.csv` (9,994 rows, 21 columns, Superstore sample dataset) and a README.

### Flow (`python auditor.py`)
1. **Config.** `INPUT_FILE` and `OUTPUT_FILE` are hard-coded. Running the script creates `output/`.
2. **Load.** Reads the CSV as `latin-1` and parses `Order Date` / `Ship Date` as `%m/%d/%Y`.
3. **Checks.** 11 functions, each returning `(status, message, detail_df)` where `status ∈ {pass, warn, fail}`:

| # | Check | Category | Rule | Status on hit |
|---|-------|----------|------|---------------|
| 1 | Missing Values | DQ | any null in any column | fail |
| 2 | Duplicate Rows | DQ | `df.duplicated()` | fail |
| 3 | Negative Sales | DQ | `Sales <= 0` | fail |
| 4 | Negative Quantity | DQ | `Quantity <= 0` | fail |
| 5 | Discount Out of Range | DQ | `Discount < 0 or > 1` | fail |
| 6 | Ship Before Order | DQ | `Ship Date < Order Date` | fail |
| 7 | Extreme Loss Outliers | Business | `Profit < mean − 3σ` | fail |
| 8 | Extreme Profit Outliers | Business | `Profit > mean + 3σ` | warn |
| 9 | High Discount Orders | Business | `Discount > 0.5` | warn |
| 10 | Discount-Driven Losses | Business | `Discount > 0.5 and Profit < 0` | warn |
| 11 | Unexplained Losses | Business | `Profit < −500 and Discount <= 0.2` | warn |

4. **Console summary.** Prints `[PASS]/[WARN]/[FAIL]` and a message for each check.
5. **HTML report.** `build_report()` renders one self-contained HTML page: a score (% of checks passed), pass/warn/fail pills, a dataset meta strip, and a card per check with up to 10 detail rows.
6. **Write.** Saves the page to `output/dq_report.html`.

### Problems to fix during the refactor
Found while reading the code. These matter for testability and correctness:

- **Everything runs at import time.** Loading the data, running the checks, `os.makedirs` and writing the file all happen at module level. Importing the module therefore runs the whole pipeline, so it can't be unit-tested.
- **Wrong "more rows" row.** Checks 7–10 always append a `"... N more rows not shown"` row. When a check finds 10 rows or fewer, this shows a **negative or zero count**, e.g. `... -7 more rows not shown`.
- **Strings mixed into numeric columns.** The note row puts `""` into `Sales`, `Discount` and `Loss`, which turns those columns into `object` dtype.
- **Dead code.** `df_to_html` reads `df.attrs["total_count"]`, but nothing ever sets it, so the "Showing X of Y" note never appears.
- **Hidden global.** `check_nulls` uses the global `total_rows` instead of `len(df)`.
- **Hard-coded report metadata.** "21 columns", "2014 – 2018" and "superstore.csv" are fixed strings in the template, so they're wrong for any other file.
- **Repeated rules.** The mean and 3σ math is duplicated, and so is the "take the top 10, convert Profit to Loss, add a note row" block. Thresholds (0.5, 0.2, −500, 3σ) are magic numbers.
- **No HTML escaping.** Product names and messages go into the page unescaped, so values containing `<`, `&` or quotes can break the markup.
- **No input checks.** A missing column fails with a raw `KeyError`. There's no schema check.
- **No CLI, logging or exit codes.** You can't point the tool at another file, and it can't fail a CI job when the data fails.
- **Score ignores warnings.** Checks with status `warn` count as "not passed". Keep this behaviour, but document it.

## 2. Target repo layout

```
sales-dq-auditor/
├── pyproject.toml            # uv-managed; project metadata, deps, ruff/pytest/mypy config
├── uv.lock
├── .python-version           # 3.12
├── .pre-commit-config.yaml
├── .gitignore / .gitattributes
├── README.md                 # updated: uv setup, CLI usage, dev workflow
├── docx/
│   └── plan.md               # this file
├── data/
│   └── superstore.csv
├── src/
│   └── sales_dq_auditor/
│       ├── __init__.py       # __version__
│       ├── __main__.py       # `python -m sales_dq_auditor`
│       ├── cli.py            # argparse entry point → `dq-audit`
│       ├── config.py         # AuditConfig dataclass (thresholds, sample size, paths)
│       ├── loader.py         # load_sales_data(), schema/required-column validation
│       ├── models.py         # Status enum, CheckResult dataclass, AuditReport
│       ├── checks/
│       │   ├── __init__.py   # registry: ALL_CHECKS list
│       │   ├── quality.py    # checks 1–6
│       │   └── business.py   # checks 7–11
│       ├── runner.py         # run_checks(df, config) -> AuditReport
│       └── report/
│           ├── __init__.py
│           ├── html.py       # render_html(report) with html.escape
│           ├── console.py    # print summary
│           └── template.html # CSS/HTML moved out of the f-string (string.Template)
└── tests/
    ├── conftest.py           # fixtures: clean_df, dirty_df factories, tmp CSV
    ├── test_loader.py
    ├── test_quality_checks.py
    ├── test_business_checks.py
    ├── test_runner.py
    ├── test_report_html.py
    ├── test_cli.py
    └── test_integration_superstore.py   # full run on real CSV, asserts known README findings
```

## 3. Design decisions

- **`CheckResult` dataclass.** Replaces the bare tuple with `name`, `category`, `status: Status`, `message`, `details: pd.DataFrame`, `total_flagged: int` and `metrics: dict` (for example `total_loss`).
- **Pure check functions.** Each check has the signature `(df, config) -> CheckResult`. No globals, no I/O.
- **Truncation in one place.** The check returns all flagged rows plus `total_flagged`. The report layer limits the table to `config.sample_size` (default 10) and prints "Showing 10 of 856 rows". This removes the fake note row and the negative-count bug, and brings back the dead `attrs` feature properly.
- **`AuditConfig`.** Holds `high_discount=0.5`, `low_discount=0.2`, `unexplained_loss=-500`, `sigma=3.0` and `sample_size=10`. Every default matches today's behaviour, so the results stay identical.
- **Report metadata from the data.** Column count, date range and file name are computed from the dataframe and file path.
- **CLI.** `dq-audit --input data/superstore.csv --output output/dq_report.html [--fail-on {fail,warn,never}]`. The exit code is non-zero according to `--fail-on`, so the tool can act as a gate in CI.
- **Logging.** Use the `logging` module for load and progress messages. The `rich`-free console summary goes to stdout.
- **Dependencies.** Runtime: `pandas`, `numpy`. Dev group: `pytest`, `pytest-cov`, `ruff`, `mypy`, `pandas-stubs`, `pre-commit`.

## 4. Tooling

### uv
- `uv init --package` style layout, `requires-python = ">=3.11"`, pin `.python-version` to 3.12.
- `[project.scripts] dq-audit = "sales_dq_auditor.cli:main"`.
- `[dependency-groups] dev = [...]`. Set up with `uv sync`, run with `uv run dq-audit` and `uv run pytest`.

### Ruff (lint and format)
- `line-length = 100`, `target-version = "py311"`.
- Rule sets: `E, W, F, I, B, UP, SIM, N, C4, PL, RUF, PD, PT, S` (ignore `S101` in tests).
- `ruff format` replaces black.

### mypy
- Strict on `src/`, with `pandas-stubs` installed.

### pre-commit (`.pre-commit-config.yaml`)
- `pre-commit-hooks`: trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-added-large-files (excluding `data/superstore.csv`), check-merge-conflict, mixed-line-ending.
- `astral-sh/ruff-pre-commit`: `ruff check --fix` and `ruff format`.
- `astral-sh/uv-pre-commit`: `uv-lock`, which keeps `uv.lock` in sync.
- Local hook for `mypy`, run through `uv run`.
- Optional local hook for `pytest` at `pre-push` stage only, so commits stay fast.

### CI (optional, recommended)
- `.github/workflows/ci.yml`: `astral-sh/setup-uv` → `uv sync` → `ruff check` → `ruff format --check` → `mypy` → `pytest --cov`.

## 5. Test plan (pytest)

Fixtures in `conftest.py` build small, hand-made DataFrames with the 21 Superstore columns. A `make_df(**overrides)` factory produces dirty variants.

| Area | Cases |
|------|-------|
| **loader** | parses dates; latin-1 file loads; missing required column raises `SchemaError`; bad date format raises a clear error |
| **check_nulls** | clean → pass; nulls in 2 columns → fail, detail has the right counts and % uses `len(df)` |
| **check_duplicates** | none → pass; exact duplicate → fail with count 1 |
| **negative sales / quantity** | boundary: `0` fails, `0.01` passes, negatives fail |
| **discount range** | `0` and `1` pass; `-0.1` and `1.1` fail |
| **ship before order** | same day passes; one day earlier fails |
| **extreme losses / gains** | constructed distribution with a known outlier; no outlier → pass; status fail vs warn; `total_loss` metric |
| **high discount** | `0.5` exactly is not flagged (strict `>`); total loss counts only negative-profit rows |
| **discount-driven losses** | needs both conditions; high discount with positive profit not flagged |
| **unexplained losses** | `-500` exactly not flagged; `0.2` discount is flagged (`<=`) |
| **regression** | ≤10 flagged rows → no negative "more rows" text anywhere |
| **runner** | runs all 11 checks in order; score maths (pass/total); warnings don't count as pass |
| **HTML report** | contains every check name; badge per status; `<script>` in product name is escaped; "Showing 10 of N" shown only when truncated; column count and date range come from data |
| **CLI** | `--input`/`--output` writes file to `tmp_path`; exit code respects `--fail-on`; missing input → non-zero with message |
| **integration** | real `superstore.csv`: 6 DQ checks pass, 856 high-discount orders, 37 extreme loss outliers, 2 unexplained losses (matches README findings) |

Coverage target: **≥ 90%** on `src/`, enforced with `--cov-fail-under=90`.

## 6. Execution steps

1. Add `pyproject.toml` with uv. Move code into `src/sales_dq_auditor/`. Keep `auditor.py` as a thin wrapper for now so the old command still works, or delete it (your call).
2. Add the models, config and loader.
3. Port the 11 checks as pure functions, fixing the bugs in §1.
4. Move the HTML template out of the f-string, add escaping, and compute the metadata from the data.
5. Add the CLI, logging and exit codes.
6. Write the pytest suite, starting with the integration test as a regression baseline before the refactor.
7. Add the ruff, mypy and pre-commit config. Run `pre-commit run --all-files` and fix what it finds.
8. Update the README for the uv workflow. Optionally add the GitHub Actions CI file.
9. Check that the generated report matches the current one: same statuses and counts on `superstore.csv`.

## 7. Open questions

- Delete `auditor.py`, or keep it as a backward-compatible wrapper?
- Add GitHub Actions CI now, or keep to local tooling only?
- Is `mypy` wanted, or is ruff enough?
- The README says notebooks, but the repo has none. Is there a notebook version somewhere else that should be included?


## Deferred: Power BI cleanup
- [ ] Step 3: rewrite `src/sales_dq_auditor/export_flags.py` to reuse the shared rules and thresholds, fix its data path, keep the same output columns.
- [ ] Before Step 9: merge `origin/main` into this branch; remove `scripts/export_flags.py`.
- [ ] Before Step 9: remove or wrap `auditor.py`.
- [ ] Update the README and check that the dashboard still refreshes.
- [ ] Do all of the above before adding the project to my CV.

- **Likely wrong encoding.** The CSV is read as `latin-1`, but it contains bytes `0x93`/`0x94`, which are curly quotes in `cp1252`. Switch in a separate commit after tests exist.


- **Profit shown as loss (fixed in Step 3b).** High Discount used `abs(Profit)` for the Loss column, so a profitable discounted order would show as a loss. Profitable rows now show 0.