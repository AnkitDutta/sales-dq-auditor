import pandas as pd
import pytest

from sales_dq_auditor.loader import SchemaError, load_sales_data


def test_parses_dates(make_df, write_csv):
    df = load_sales_data(write_csv(make_df()))

    assert df["Order Date"].iloc[0] == pd.Timestamp("2017-01-10")
    assert df["Ship Date"].iloc[0] == pd.Timestamp("2017-01-12")


def test_reads_latin1_characters(make_df, write_csv):
    df = load_sales_data(write_csv(make_df(rows=1, Product_Name="Café chair")))

    assert df["Product Name"].iloc[0] == "Café chair"


def test_missing_columns_are_all_reported(make_df, write_csv):
    path = write_csv(make_df().drop(columns=["Profit", "Sales"]))

    with pytest.raises(SchemaError, match="Sales, Profit"):
        load_sales_data(path)


def test_bad_date_names_the_column(make_df, write_csv):
    path = write_csv(make_df(rows=1, Ship_Date="2017-01-12"))

    with pytest.raises(SchemaError, match="Ship Date"):
        load_sales_data(path)


def test_file_without_rows_is_rejected(make_df, write_csv):
    path = write_csv(make_df(rows=0))

    with pytest.raises(SchemaError, match="no data rows"):
        load_sales_data(path)
