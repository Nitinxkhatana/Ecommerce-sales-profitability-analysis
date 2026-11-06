"""
Stage 1 - Data profiling of the raw Superstore dataset.
Reports the ACTUAL quality issues found (no assumptions).
Run:  python python/profile_data.py
"""

import pandas as pd

RAW_PATH = "data/raw/Sample - Superstore.csv"

df = pd.read_csv(RAW_PATH, encoding="cp1252")

print(f"shape: {df.shape}")

print("\n--- dtypes ---")
print(df.dtypes.to_string())

print("\n--- missing values per column ---")
miss = df.isna().sum()
print((miss[miss > 0].to_string()) if miss.sum() > 0 else "none")

d_full = df.duplicated().sum()
d_rowid = df.duplicated(subset=["Row ID"]).sum()
d_orderprod = df.duplicated(subset=["Order ID", "Product ID"]).sum()
print(f"\n--- duplicates: full rows = {d_full} | Row ID = {d_rowid} | Order ID+Product ID = {d_orderprod}")

print(f"\n--- Order Date range: {df['Order Date'].min()} to {df['Order Date'].max()}")
print(f"--- Ship Date range:  {df['Ship Date'].min()} to {df['Ship Date'].max()}")

cats = ["Order ID", "Customer ID", "Customer Name", "Product ID", "Product Name",
        "Region", "Category", "Sub-Category", "Segment", "Ship Mode", "State", "City", "Country"]
print("\n--- unique counts ---")
print(df[cats].nunique().to_string())

print("\n--- numeric summary ---")
print(df[["Sales", "Quantity", "Discount", "Profit"]].describe().round(2).to_string())

print("\n--- data quality checks ---")
print(f"Discount values: {sorted(df['Discount'].unique())}")
print(f"Rows with Discount > 0.5: {(df['Discount'] > 0.5).sum()}")
print(f"Rows with Profit < 0:    {(df['Profit'] < 0).sum()}")
print(f"Rows with Sales < 0:     {(df['Sales'] < 0).sum()}")
print(f"Rows with Sales == 0:    {(df['Sales'] == 0).sum()}")
bad_qty = ((df["Quantity"] <= 0) | (df["Quantity"] % 1 != 0)).sum()
print(f"Rows with invalid Quantity: {bad_qty}")
print(f"Sales with trailing '$'/commas (object dtype): {df['Sales'].dtype == object}")
postal_na = df["Postal Code"].isna().sum()
zero_decimal_rows = df["Postal Code"].astype(str).str.len().lt(5).sum() - postal_na
print(f"Postal Code: missing = {postal_na}, possibly truncated/short = {max(zero_decimal_rows,0)}")

# ship date before order date?
import numpy as np
od = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
sd = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
print(f"Rows where Ship Date < Order Date: {(sd < od).sum()}")
