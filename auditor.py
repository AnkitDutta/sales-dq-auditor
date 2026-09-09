import pandas as pd
import numpy as np
from datetime import datetime
import os

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
INPUT_FILE  = "data/superstore.csv"
OUTPUT_FILE = "output/dq_report.html"
os.makedirs("output", exist_ok=True)

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
df = pd.read_csv(INPUT_FILE, encoding="latin-1")
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  format="%m/%d/%Y")

total_rows = len(df)
print(f"Loaded {total_rows:,} rows, {len(df.columns)} columns")

# ─────────────────────────────────────────
# CHECK FUNCTIONS
# Each returns: (status, summary_message, detail_dataframe)
# status: "pass" | "warn" | "fail"
# ─────────────────────────────────────────

def check_nulls(df):
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if null_counts.empty:
        return "pass", "No missing values across all 21 columns.", pd.DataFrame()
    detail = null_counts.reset_index()
    detail.columns = ["Column", "Null Count"]
    detail["% of Rows"] = (detail["Null Count"] / total_rows * 100).round(2)
    return "fail", f"{len(null_counts)} column(s) contain missing values.", detail


def check_duplicates(df):
    dupes = df[df.duplicated()]
    if dupes.empty:
        return "pass", "No duplicate rows found.", pd.DataFrame()
    return "fail", f"{len(dupes):,} fully duplicate row(s) detected.", dupes.head(10)


def check_negative_sales(df):
    bad = df[df["Sales"] <= 0]
    if bad.empty:
        return "pass", "All Sales values are positive.", pd.DataFrame()
    return "fail", f"{len(bad):,} row(s) with zero or negative Sales.", \
        bad[["Order ID", "Product Name", "Category", "Sales"]].head(10)


def check_negative_quantity(df):
    bad = df[df["Quantity"] <= 0]
    if bad.empty:
        return "pass", "All Quantity values are positive.", pd.DataFrame()
    return "fail", f"{len(bad):,} row(s) with zero or negative Quantity.", \
        bad[["Order ID", "Product Name", "Quantity"]].head(10)


def check_discount_range(df):
    bad = df[(df["Discount"] < 0) | (df["Discount"] > 1)]
    if bad.empty:
        return "pass", "All Discount values fall within the valid 0–1 range.", pd.DataFrame()
    return "fail", f"{len(bad):,} row(s) with Discount outside 0–1.", \
        bad[["Order ID", "Product Name", "Discount"]].head(10)


def check_ship_before_order(df):
    bad = df[df["Ship Date"] < df["Order Date"]]
    if bad.empty:
        return "pass", "No orders found where Ship Date precedes Order Date.", pd.DataFrame()
    return "fail", f"{len(bad):,} row(s) where Ship Date is before Order Date.", \
        bad[["Order ID", "Order Date", "Ship Date"]].head(10)


def check_extreme_losses(df):
    mean   = df["Profit"].mean()
    stddev = df["Profit"].std()
    bad    = df[df["Profit"] < mean - 3 * stddev].copy()
    if bad.empty:
        return "pass", "No extreme loss outliers detected.", pd.DataFrame()
    total_count = len(bad)
    total_loss  = bad["Profit"].sum()
    result = bad[["Order ID", "Product Name", "Category", "Sales", "Discount", "Profit"]].head(10).copy()
    result["Loss"] = result["Profit"].abs().round(4)
    result = result.drop(columns=["Profit"])
    note_row = pd.DataFrame([{
        "Order ID": f"... {total_count - 10:,} more rows not shown",
        "Product Name": "", "Category": "", "Sales": "", "Discount": "", "Loss": ""
    }])
    result = pd.concat([result, note_row], ignore_index=True)
    return "fail", \
        f"{total_count:,} order(s) with losses beyond 3 standard deviations from mean profit. Total loss: ${abs(total_loss):,.2f}.", \
        result


def check_extreme_gains(df):
    mean   = df["Profit"].mean()
    stddev = df["Profit"].std()
    good   = df[df["Profit"] > mean + 3 * stddev].copy()
    if good.empty:
        return "pass", "No unusually high profit outliers detected.", pd.DataFrame()
    total_count = len(good)
    result = good[["Order ID", "Product Name", "Category", "Sales", "Discount", "Profit"]].head(10).copy()
    note_row = pd.DataFrame([{
        "Order ID": f"... {total_count - 10:,} more rows not shown",
        "Product Name": "", "Category": "", "Sales": "", "Discount": "", "Profit": ""
    }])
    result = pd.concat([result, note_row], ignore_index=True)
    return "warn", \
        f"{total_count:,} order(s) with profit beyond 3 standard deviations above mean — validate these are not data entry errors.", \
        result


def check_high_discount(df):
    bad = df[df["Discount"] > 0.5].copy()
    if bad.empty:
        return "pass", "No discounts above 50% found.", pd.DataFrame()
    total_count = len(bad)
    total_loss  = bad[bad["Profit"] < 0]["Profit"].sum()
    result      = bad[["Order ID", "Product Name", "Discount", "Profit"]].head(10).copy()
    result["Loss"] = result["Profit"].abs().round(4)
    result = result.drop(columns=["Profit"])
    note_row = pd.DataFrame([{
        "Order ID": f"... {total_count - 10:,} more rows not shown",
        "Product Name": "", "Discount": "", "Loss": ""
    }])
    result = pd.concat([result, note_row], ignore_index=True)
    return "warn", \
        f"{total_count:,} order(s) with Discount above 50%. Those with negative profit represent ${abs(total_loss):,.2f} in losses.", \
        result


def check_discount_driven_losses(df):
    bad = df[(df["Discount"] > 0.5) & (df["Profit"] < 0)].copy()
    if bad.empty:
        return "pass", "No high-discount orders with negative profit found.", pd.DataFrame()
    total_count = len(bad)
    total_loss  = bad["Profit"].sum()
    result = bad[["Order ID", "Product Name", "Category", "Sales", "Discount", "Profit"]].head(10).copy()
    result["Loss"] = result["Profit"].abs().round(4)
    result = result.drop(columns=["Profit"])
    note_row = pd.DataFrame([{
        "Order ID": f"... {total_count - 10:,} more rows not shown",
        "Product Name": "", "Category": "", "Sales": "", "Discount": "", "Loss": ""
    }])
    result = pd.concat([result, note_row], ignore_index=True)
    return "warn", \
        f"{total_count:,} order(s) with Discount >50% and negative Profit. Discount policy is directly driving ${abs(total_loss):,.2f} in losses.", \
        result


def check_unexplained_losses(df):
    bad = df[(df["Profit"] < -500) & (df["Discount"] <= 0.2)].copy()
    if bad.empty:
        return "pass", "No significant losses found outside of discount policy.", pd.DataFrame()
    total_loss = bad["Profit"].sum()
    result = bad[["Order ID", "Product Name", "Category", "Sales", "Discount", "Profit"]].head(10).copy()
    result["Loss"] = result["Profit"].abs().round(4)
    result = result.drop(columns=["Profit"])
    return "warn", \
        f"{len(bad):,} order(s) with Loss above $500 at ≤20% discount — losses not explained by discounting alone. Total: ${abs(total_loss):,.2f}. Possible cost basis or pricing issue.", \
        result


# ─────────────────────────────────────────
# RUN ALL CHECKS
# ─────────────────────────────────────────
checks = [
    ("Missing Values",                  check_nulls(df)),
    ("Duplicate Rows",                  check_duplicates(df)),
    ("Negative Sales",                  check_negative_sales(df)),
    ("Negative Quantity",               check_negative_quantity(df)),
    ("Discount Out of Range",           check_discount_range(df)),
    ("Ship Date Before Order Date",     check_ship_before_order(df)),
    ("Extreme Loss Outliers",           check_extreme_losses(df)),
    ("Extreme Profit Outliers",         check_extreme_gains(df)),
    ("High Discount Orders (>50%)",     check_high_discount(df)),
    ("Discount-Driven Losses",          check_discount_driven_losses(df)),
    ("Unexplained Losses",              check_unexplained_losses(df)),
]

print("\nCheck Results")
print("─" * 55)
for name, (status, message, _) in checks:
    icon = "PASS" if status == "pass" else "WARN" if status == "warn" else "FAIL"
    print(f"[{icon}]  {name}")
    print(f"       {message}")

# ─────────────────────────────────────────
# HTML REPORT
# ─────────────────────────────────────────

def status_badge(status):
    styles = {
        "pass": ("background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0", "Pass"),
        "warn": ("background:#fffbeb;color:#92400e;border:1px solid #fcd34d", "Warning"),
        "fail": ("background:#fef2f2;color:#991b1b;border:1px solid #fca5a5", "Fail"),
    }
    style, label = styles[status]
    return f'<span style="{style};padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;letter-spacing:0.03em">{label}</span>'


def df_to_html(df):
    if df.empty:
        return ""
    total = df.attrs.get("total_count", None)
    note  = f'<p class="table-note">Showing {len(df)} of {total:,} rows</p>' if total else ""
    return note + df.to_html(index=False, border=0, classes="detail-table")


def build_report(checks, total_rows, generated_at):
    passed  = sum(1 for _, (s, _, __) in checks if s == "pass")
    warned  = sum(1 for _, (s, _, __) in checks if s == "warn")
    failed  = sum(1 for _, (s, _, __) in checks if s == "fail")
    total   = len(checks)
    score   = round(passed / total * 100)

    checks_html = ""
    for name, (status, message, detail_df) in checks:
        detail_html = df_to_html(detail_df)
        if detail_html:
            detail_html = f'<div class="detail-wrap">{detail_html}</div>'
        checks_html += f"""
        <div class="check-row">
            <div class="check-top">
                <span class="check-name">{name}</span>
                {status_badge(status)}
            </div>
            <p class="check-msg">{message}</p>
            {detail_html}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Report — Superstore Sales</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    background: #f7f8fa;
    color: #1a1a2e;
    padding: 48px 24px;
  }}

  .wrap {{ max-width: 860px; margin: 0 auto; }}

  /* Top bar */
  .topbar {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 36px;
    padding-bottom: 24px;
    border-bottom: 2px solid #e2e5ea;
  }}
  .topbar-left h1 {{
    font-size: 20px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 4px;
  }}
  .topbar-left p {{
    font-size: 12px;
    color: #64748b;
    font-family: 'JetBrains Mono', monospace;
  }}
  .score-block {{
    text-align: right;
  }}
  .score-number {{
    font-size: 40px;
    font-weight: 600;
    color: {('#065f46' if score >= 80 else '#92400e' if score >= 60 else '#991b1b')};
    line-height: 1;
    font-family: 'JetBrains Mono', monospace;
  }}
  .score-label {{
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
  }}

  /* Summary strip */
  .summary {{
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
  }}
  .summary-pill {{
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .pill-pass {{ background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }}
  .pill-warn {{ background:#fffbeb; color:#92400e; border:1px solid #fcd34d; }}
  .pill-fail {{ background:#fef2f2; color:#991b1b; border:1px solid #fca5a5; }}
  .pill-num  {{ font-size:16px; font-weight:600; font-family:'JetBrains Mono',monospace; }}

  /* Dataset meta */
  .meta {{
    background: white;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 28px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #475569;
    display: flex;
    gap: 32px;
  }}
  .meta span {{ color: #0f172a; font-weight: 500; }}

  /* Check rows */
  .section-label {{
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
    text-transform: uppercase;
  }}

  .check-row {{
    background: white;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 10px;
  }}
  .check-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }}
  .check-name {{
    font-weight: 600;
    font-size: 13px;
    color: #0f172a;
  }}
  .check-msg {{
    font-size: 12px;
    color: #64748b;
    margin-bottom: 0;
  }}

  /* Detail tables */
  .detail-wrap {{
    margin-top: 14px;
    overflow-x: auto;
    border-top: 1px solid #f1f5f9;
    padding-top: 12px;
  }}
  .detail-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11.5px;
    font-family: 'JetBrains Mono', monospace;
  }}
  .detail-table th {{
    text-align: left;
    padding: 6px 12px;
    font-size: 10.5px;
    font-weight: 600;
    color: #64748b;
    border-bottom: 1px solid #e2e5ea;
    white-space: nowrap;
  }}
  .table-note {{
    font-size: 11px;
    color: #94a3b8;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
  }}
  .detail-table td {{
    padding: 6px 12px;
    color: #334155;
    border-bottom: 1px solid #f8fafc;
    white-space: nowrap;
  }}
  .detail-table tr:last-child td {{ border-bottom: none; }}
  .detail-table tr:hover td {{ background: #f8fafc; }}

  /* Footer */
  .footer {{
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e2e5ea;
    font-size: 11px;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
  }}
</style>
</head>
<body>
<div class="wrap">

  <div class="topbar">
    <div class="topbar-left">
      <h1>Data Quality Report</h1>
      <p>superstore.csv &nbsp;·&nbsp; {generated_at}</p>
    </div>
    <div class="score-block">
      <div class="score-number">{score}%</div>
      <div class="score-label">checks passed</div>
    </div>
  </div>

  <div class="summary">
    <div class="summary-pill pill-pass"><span class="pill-num">{passed}</span> passed</div>
    <div class="summary-pill pill-warn"><span class="pill-num">{warned}</span> warnings</div>
    <div class="summary-pill pill-fail"><span class="pill-num">{failed}</span> failed</div>
  </div>

  <div class="meta">
    <div>Rows &nbsp;<span>{total_rows:,}</span></div>
    <div>Columns &nbsp;<span>21</span></div>
    <div>Checks run &nbsp;<span>{total}</span></div>
    <div>Date range &nbsp;<span>2014 – 2018</span></div>
  </div>

  <div class="section-label">Check Results</div>

  {checks_html}

  <div class="footer">
    <span>Sales Data Quality Auditor</span>
    <span>github.com/AnkitDutta</span>
  </div>

</div>
</body>
</html>"""
    return html


# ─────────────────────────────────────────
# WRITE REPORT
# ─────────────────────────────────────────
generated_at = datetime.now().strftime("%d %b %Y, %H:%M")
html = build_report(checks, total_rows, generated_at)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nReport saved → {OUTPUT_FILE}")