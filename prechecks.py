"""
Stage 2 pre-checks: real date range + inspect duplicate Order ID + Product ID lines.
"""

import pandas as pd

df = pd.read_csv("data/raw/Sample - Superstore.csv", encoding="cp1252")

od = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
sd = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
print(f"True Order Date range: {od.min().date()} to {od.max().date()}")
print(f"True Ship  Date range: {sd.min().date()} to {sd.max().date()}")
print(f"Rows per year:\n{od.dt.year.value_counts().sort_index().to_string()}")

dup_mask = df.duplicated(subset=["Order ID", "Product ID"])
print(f"\nDuplicates (Order ID + Product ID): {dup_mask.sum()} rows")
cols = ["Order ID", "Order Date", "Quantity", "Discount", "Sales", "Profit",
        "Region", "Product Name"]
print(df.loc[dup_mask, cols].sort_values("Order ID").to_string())

print("\nPostal Code short (leading zero states):")
short = df["Postal Code"].astype(str).str.len() < 5
print(df.loc[short, ["State", "City", "Postal Code"]].drop_duplicates().head(10).to_string())
print("Unique states with short ZIPs:", df.loc[short, "State"].unique())
