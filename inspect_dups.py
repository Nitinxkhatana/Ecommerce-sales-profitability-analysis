"""Inspect why duplicated() became non-zero after dropping Row ID."""

import pandas as pd

df = pd.read_csv("data/raw/Sample - Superstore.csv", encoding="cp1252")

# full duplicate considering everything EXCEPT Row ID
d_mask = df.drop(columns=["Row ID"]).duplicated(keep=False)
print(f"Rows that become identical (ignoring Row ID): {d_mask.sum()}")

cols = ["Row ID", "Order ID", "Order Date", "Customer ID", "Product ID",
        "Quantity", "Discount", "Sales", "Profit", "Postal Code", "Region"]
print(df.loc[d_mask, cols].sort_values(["Order ID", "Product ID"]).to_string())

# confirm raw full-file duplicates (with Row ID) are 0
print("\nFull duplicates incl. Row ID:", df.duplicated().sum())
