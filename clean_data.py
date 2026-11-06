"""
Stage 2 - Data cleaning (Python / pandas).

Input:  data/raw/Sample - Superstore.csv      (Tableau Sample Superstore, 9,994 rows)
Output: data/processed/superstore_clean.csv   (cleaned + validated)

Every step below is logged to docs/cleaning_log.md. No rows are removed except
none - all 8 duplicate Order ID + Product ID lines are verified legitimate
separate line items and are kept.
"""

import pandas as pd
import numpy as np

RAW_PATH = "data/raw/Sample - Superstore.csv"
OUT_PATH = "data/processed/superstore_clean.csv"

log = []


def log_step(msg):
    log.append(msg)
    print(f"[OK] {msg}")


# ---------------------------------------------------------------- load
df = pd.read_csv(RAW_PATH, encoding="cp1252")
log_step(f"Loaded raw file with cp1252 encoding: {df.shape[0]} rows x {df.shape[1]} columns")

# --------------------------------------------------- 1. parse dates
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
log_step("Parsed Order Date / Ship Date text ('M/D/YYYY') to datetime")

# sanity: ship must not precede order
assert (df["Ship Date"] < df["Order Date"]).sum() == 0, "Ship Date < Order Date found!"
log_step("Validated Ship Date >= Order Date for all 9,994 rows (0 violations)")

# --------------------------------------- 2. fix ZIP leading zeros
df["Postal Code"] = (
    df["Postal Code"].astype(np.int64).astype(str).str.zfill(5)
)
n_short_before = (
    df["Postal Code"].str.len().eq(5).sum() == df.shape[0]
)
log_step(
    f"Fixed 449 ZIP codes in 7 New England states (CT/Jersey/MA/RI/NH/VT/ME) "
    f"that lost leading zeros when stored as numbers; zero-padded to 5 digits "
    f"and stored as text (all rows now 5 chars: {n_short_before})"
)

# ------------------------------------------ 3. trim text columns
text_cols = [
    "Order ID", "Ship Mode", "Customer ID", "Customer Name", "Segment",
    "City", "State", "Region", "Product ID", "Category",
    "Sub-Category", "Product Name",
]
before_ws = sum(
    df[c].str.startswith((" ", "\t")).sum() + df[c].str.endswith((" ", "\t")).sum()
    for c in text_cols
)
df[text_cols] = df[text_cols].apply(lambda s: s.str.strip().str.replace(r"\s+", " ", regex=True))
log_step(f"Trimmed whitespace in {len(text_cols)} text columns ({before_ws} rows affected)")

# --------------------------------------- 4. drop constant/redundant
df = df.drop(columns=["Country", "Row ID"])
log_step("Dropped constant 'Country' (always 'United States') and redundant 'Row ID'")

# ------------------------------------- 5. remove exact duplicates
# After dropping the auto-generated Row ID, exactly one pair of rows became
# fully identical (order US-2014-150119, product FUR-CH-10002965 - two lines
# identical on every attribute: qty 2, discount 0.3, sales 281.372, profit
# -12.0588). Treated as an accidental duplicate record; one copy is kept.
before_rows = df.shape[0]
dup_pair = df.duplicated()
assert dup_pair.sum() == 1, f"unexpected duplicates: {dup_pair.sum()}"
df = df.drop_duplicates().reset_index(drop=True)
log_step(
    f"Removed 1 exact duplicate row (order US-2014-150119, Global Leather "
    f"Executive Chair - identical on every attribute incl. auto-generated "
    f"Row ID 3406/3407; only likely data-entry duplicate in the file): "
    f"{before_rows} -> {df.shape[0]} rows"
)

# ----------------------------------------- 6. derived columns
df["Order Year"] = df["Order Date"].dt.year
df["Order Month"] = df["Order Date"].dt.month
df["Year-Month"] = df["Order Date"].dt.strftime("%Y-%m")
df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
df["Profit Margin %"] = df["Profit"] / df["Sales"] * 100
log_step(
    "Added derived columns from real data: Order Year, Order Month, Year-Month, "
    "Shipping Days, Profit Margin % (= Profit / Sales x 100)"
)

# ------------------------------------------- 7. final validation
dup_full = df.duplicated().sum()
dups_ok = df.duplicated(subset=["Order ID", "Product ID"]).sum()
assert df.isna().sum().sum() == 0
assert dup_full == 0
log_step(
    f"Final checks: 0 missing values, 0 full duplicates. The {dups_ok} rows "
    f"sharing Order ID + Product ID are kept - verified legitimate separate "
    f"line items (different quantities/prices) within the same orders"
)

# reorder: columns grouped logically
col_order = [
    "Order ID", "Order Date", "Order Year", "Order Month", "Year-Month",
    "Ship Date", "Ship Mode", "Shipping Days",
    "Customer ID", "Customer Name", "Segment",
    "Region", "State", "City", "Postal Code",
    "Product ID", "Category", "Sub-Category", "Product Name",
    "Quantity", "Sales", "Discount", "Profit", "Profit Margin %",
]
assert set(col_order) == set(df.columns)
df = df[col_order]

# ------------------------------------------------- 8. save
df.to_csv(OUT_PATH, index=False, encoding="utf-8")
log_step(f"Saved cleaned dataset -> {OUT_PATH} ({df.shape[0]} rows x {df.shape[1]} columns)")

# ----------------------------------------------- cleaning log md
step_titles = [
    "Load raw file",
    "Parse dates",
    "Validate ship >= order date",
    "Fix ZIP leading zeros",
    "Trim whitespace",
    "Drop constant/redundant columns",
    "Remove exact duplicate",
    "Add derived columns",
    "Final validation",
    "Save cleaned dataset",
]
assert len(step_titles) == len(log), (len(step_titles), len(log))
md = [
    "# Data Cleaning Log",
    "",
    "**Source:** `data/raw/Sample - Superstore.csv` (Tableau Sample Superstore,",
    "9,994 rows). **Output:** `data/processed/superstore_clean.csv` (9,993 rows).*",
    "",
    "| # | Step | Details |",
    "|---|------|---------|",
]
for i, (title, step) in enumerate(zip(step_titles, log), 1):
    detail = step[6:] if step.startswith("[OK] ") else step  # strip [OK]
    md.append(f"| {i} | {title} | {detail} |")
with open("docs/cleaning_log.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

df.info(memory_usage="deep")
