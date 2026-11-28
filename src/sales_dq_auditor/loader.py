"""Load the sales CSV and validate its shape."""


from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = (
    "Order ID",
    "Order Date",
    "Ship Date",
    "Product Name",
    "Category",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
)
DATE_COLUMNS = ("Order Date", "Ship Date")
DATE_FORMAT = "%m/%d/%Y"

class SchemaError(ValueError):
    """The input file doesn't have the columns or formats we expect"""
    
def load_sales_data(path: Path) -> pd.DataFrame:
    """Read a sales CSV, check required columns and parse the dates."""
    df = pd.read_csv(path, encoding="latin-1")
    
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise SchemaError(f"Missing required column(s): {', '.join(missing)}")
    if df.empty:
        raise SchemaError("The file has no data rows.")
    
    for column in DATE_COLUMNS:
        try:
            df[column] = pd.to_datetime(df[column], format=DATE_FORMAT)
        except ValueError as err:
            raise SchemaError(f"Bad date in '{column}', expected MM/DD/YYYY: {err}") from err
    return df