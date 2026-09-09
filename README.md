# Sales Data Quality Auditor

## Overview
A Python tool that ingests a sales dataset, runs data quality and
business rule checks, and produces a self-contained HTML report with flagged
issues, detail tables, and a summary scorecard.

Built to mirror real-world data validation workflows — the kind used in sales
operations and compensation environments where bad data directly causes incorrect
payouts or reporting errors.

**Tools used:** Python, pandas, numpy, GitHub

---

## What It Does
The auditor runs 11 checks across two categories:

**Data Quality Checks**
- Missing values across all columns
- Fully duplicate rows
- Negative or zero Sales values
- Negative or zero Quantity values
- Discount values outside valid 0–1 range
- Ship Date preceding Order Date

**Business Rule Checks**
- Extreme loss outliers (below 3 standard deviations from mean profit)
- Extreme profit outliers (above 3 standard deviations from mean profit)
- High discount orders (>50%) and their impact on margin
- Discount-driven losses (orders where high discount directly caused negative profit)
- Unexplained losses (significant losses at low discount — potential pricing or cost basis issues)

---

## Sample Output
<img width="1902" height="988" alt="image" src="https://github.com/user-attachments/assets/e39e0baf-3baf-468c-adb3-5b66810f35f7" />

---

## Key Findings on Superstore Dataset

### 1. Discount Policy is the Primary Driver of Losses
856 orders (8.6% of all transactions) carried discounts above 50%.
Of these, a significant portion resulted in negative profit — meaning the
business was effectively paying customers to take products. Total losses
from discount-driven orders exceeded $76K.

### 2. Unexplained Losses in Office Supplies
2 high-value orders ($4,663 and $3,930 in Sales) recorded losses above
$500 despite only 20% discounts applied. Both were electric letter opener
SKUs. Losses of this magnitude at modest discount levels suggest potential
cost basis errors or pricing misalignment — not discount policy — and would
warrant investigation with inventory/cost data.

### 3. 37 Extreme Loss Outliers Totalling $58K
Statistical outlier detection (3σ method) flagged 37 orders with losses
beyond 3 standard deviations from mean profit ($28.66 ± $234.26).
The worst single order lost $3,839 on $7,999 in sales — a -48% margin
on a 50% discounted 3D printer.

### 4. Data Integrity is Clean
No missing values, duplicate rows, invalid date sequences, or out-of-range
values were found. All quality issues are business rule violations rather
than structural data problems.

---

## How to Run

**Install dependencies:**
```bash
pip install pandas numpy
```

**Run the auditor:**
```bash
python auditor.py
```

**View the report:**
Open `output/dq_report.html` in any browser.

---

## Project Structure
