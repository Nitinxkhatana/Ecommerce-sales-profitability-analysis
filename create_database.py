"""
Stage 3 - Build the SQLite database from the cleaned dataset.

Input:  data/processed/superstore_clean.csv   (9,993 rows x 24 cols)
Output: data/ecommerce.db  (table: superstore, with indexes)
"""

import sqlite3
import pandas as pd

DB_PATH = "data/ecommerce.db"

df = pd.read_csv(
    "data/processed/superstore_clean.csv",
    encoding="utf-8",
    parse_dates=["Order Date", "Ship Date"],
    dtype={"Postal Code": str},  # keep leading zeros (ZIP codes are codes, not numbers)
)

conn = sqlite3.connect(DB_PATH)

# SQL-friendly column names: non-alphanumeric chars -> underscores (DB only)
df.columns = (
    df.columns.astype(str)
    .str.replace(r"\W+", "_", regex=True)
    .str.rstrip("_")               # 'Profit Margin %' -> 'Profit_Margin__' fix
    .str.replace("Profit_Margin", "Profit_Margin_Pct", regex=False)
)

df.to_sql("superstore", conn, if_exists="replace", index=False)

# index the columns the analysis queries filter / join on
for idx_name, col in [
    ("idx_orders_date", "Order_Date"),
    ("idx_orders_yearmonth", "Year_Month"),
    ("idx_orders_customer", "Customer_ID"),
    ("idx_orders_product", "Product_ID"),
    ("idx_orders_region", "Region"),
    ("idx_orders_category", "Category"),
    ("idx_orders_orderid", "Order_ID"),
]:
    conn.execute(f"CREATE INDEX {idx_name} ON superstore ({col})")
conn.commit()

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM superstore")
n = cur.fetchone()[0]
print(f"table 'superstore' loaded: {n} rows")

cur.execute("PRAGMA table_info(superstore)")
for _, name, ctype, *_ in cur.fetchall():
    print(f"  {name:<17} {ctype}")

conn.close()
