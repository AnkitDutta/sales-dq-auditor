import pandas as pd

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # src/ -> project root
INPUT_FILE = ROOT / "data" / "superstore.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(INPUT_FILE, encoding="latin-1")

df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  format="%m/%d/%Y")

mean, sd = df["Profit"].mean(), df["Profit"].std()

# same rules as auditor.py, but as True/False columns on every row
df["flag_extreme_loss"]    = df["Profit"] < mean - 3 * sd
df["flag_extreme_gain"]    = df["Profit"] > mean + 3 * sd
df["flag_high_discount"]   = df["Discount"] > 0.5
df["flag_discount_loss"]   = (df["Discount"] > 0.5) & (df["Profit"] < 0)
df["flag_unexplained_loss"] = (df["Profit"] < -500) & (df["Discount"] <= 0.2)

flag_cols = [c for c in df.columns if c.startswith("flag_")]
df["flag_count"] = df[flag_cols].sum(axis=1)

df.to_csv(OUTPUT_DIR / "superstore_flagged.csv", index=False)
print(df[flag_cols].sum())