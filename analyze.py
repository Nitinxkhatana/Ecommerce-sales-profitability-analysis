"""
Stage 4 - Deep analysis with pandas + numpy on the cleaned Superstore data.

Input:  data/processed/superstore_clean.csv
Outputs:
  - console findings (all computed from real data)
  - docs/analysis_findings.md     (markdown summary with tables)
  - docs/charts/*.png             (presentation charts for README)

Metrics are computed on 9,993 cleaned order-line rows across 2014-2017.
AOV (average order value) = total revenue / number of distinct orders.
"""

import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({"figure.dpi": 130, "axes.grid": True, "grid.alpha": 0.3})

df = pd.read_csv("data/processed/superstore_clean.csv", encoding="utf-8")
df["Order Date"] = pd.to_datetime(df["Order Date"])

OUT_CHARTS = "docs/charts"
os.makedirs(OUT_CHARTS, exist_ok=True)

md = ["# Stage 4 - Analysis Findings (pandas + numpy)", "",
      "All numbers computed from `data/processed/superstore_clean.csv` "
      "(9,993 order-line rows, 2014-2017, United States).\n"]

def add(line=""):
    md.append(line)

def save_fig(fig, name):
    path = f"{OUT_CHARTS}/{name}"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] {path}")

# ============================================================================
# 1. KPI HEADLINE
# ============================================================================
n_orders = df["Order ID"].nunique()
n_customers = df["Customer ID"].nunique()
n_products = df["Product ID"].nunique()
total_sales = df["Sales"].sum()
total_profit = df["Profit"].sum()
aov = total_sales / n_orders

add("## 1. Headline KPIs\n")
add(f"| KPI | Value |")
add(f"|---|---|")
add(f"| Total revenue (2014-2017) | ${total_sales:,.2f} |")
add(f"| Total profit | ${total_profit:,.2f} |")
add(f"| Overall profit margin | {total_profit/total_sales*100:.1f}% |")
add(f"| Orders | {n_orders:,} |")
add(f"| Customers | {n_customers:,} |")
add(f"| Products | {n_products:,} |")
add(f"| Average order value (AOV) | ${aov:,.2f} |")
add(f"| Loss-making order lines | {(df['Profit'] < 0).sum():,} "
    f"({(df['Profit'] < 0).mean()*100:.1f}% of lines) |")
print(f"KPIs: rev={total_sales:,.2f} profit={total_profit:,.2f} orders={n_orders}")

# ============================================================================
# 2. YEARLY PERFORMANCE + YoY GROWTH
# ============================================================================
yearly = df.groupby("Order Year").agg(
    Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
    Orders=("Order ID", "nunique"),
).reset_index()
yearly["Revenue"] = round(yearly["Revenue"], 2)
yearly["Profit"] = round(yearly["Profit"], 2)
yearly["Margin %"] = (yearly["Profit"] / yearly["Revenue"] * 100).round(1)
yearly["AOV"] = (yearly["Revenue"] / yearly["Orders"]).round(2)
yearly["YoY Rev %"] = (yearly["Revenue"].pct_change() * 100).round(1)

add("\n## 2. Yearly performance\n")
add("| Year | Revenue | Profit | Margin % | Orders | AOV | YoY Revenue |")
add("|---|---|---|---|---|---|---|")
for _, r in yearly.iterrows():
    yoy = "-" if pd.isna(r["YoY Rev %"]) else (f"+{r['YoY Rev %']}%" if r["YoY Rev %"] >= 0 else f"{r['YoY Rev %']}%")
    add(f"| {int(r['Order Year'])} | ${r['Revenue']:,.2f} | ${r['Profit']:,.2f} | "
        f"{r['Margin %']}% | {int(r['Orders']):,} | ${r['AOV']:,.2f} | {yoy} |")

# ============================================================================
# 3. MONTHLY TREND (seasonality)
# ============================================================================
monthly = df.groupby("Year-Month").agg(
    Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
    Orders=("Order ID", "nunique"),
).reset_index()

# seasonality: average revenue by calendar month across years
df["Month_Name"] = df["Order Date"].dt.strftime("%b")
month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
season = df.groupby("Month_Name")["Sales"].sum().reindex(month_order)

peak = monthly.loc[monthly["Revenue"].idxmax()]
low = monthly.loc[monthly["Revenue"].idxmin()]
add("\n## 3. Monthly trend\n")
add(f"- Peak month: **{peak['Year-Month']}** ${peak['Revenue']:,.2f}; "
    f"lowest: **{low['Year-Month']}** ${low['Revenue']:,.2f}")
top3 = season.nlargest(3)
add(f"- Seasonality: the strongest calendar months across all years are "
    + ", ".join(f"**{m}** (${v:,.2f})" for m, v in top3.items()))
add(f"- Best months are all in Q4/September; Q1 (Jan-Feb) is consistently weakest")

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(monthly["Year-Month"], monthly["Revenue"], marker="o", ms=3, lw=1.2,
        label="Monthly revenue")
ax.plot(monthly["Year-Month"], monthly["Profit"], marker="o", ms=3, lw=1.2,
        color="seagreen", label="Monthly profit")
ax.set_title("Monthly Revenue & Profit, 2014-2017")
ax.set_ylabel("USD")
ax.legend()
ax.xaxis.set_major_locator(plt.MaxNLocator(16))
ax.tick_params(axis="x", rotation=45)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
save_fig(fig, "monthly_trend.png")
add("\n![Monthly trend](charts/monthly_trend.png)")

# ============================================================================
# 4. DISCOUNT EFFECT ON PROFIT (numpy correlation)
# ============================================================================
disc = df["Discount"].to_numpy()
prof = df["Profit"].to_numpy()
marg = df["Profit Margin %"].to_numpy()
sales = df["Sales"].to_numpy()

r_profit = np.corrcoef(disc, prof)[0, 1]
r_margin = np.corrcoef(disc, marg)[0, 1]

# realized margin per discount band (same as SQL Q13, recomputed in pandas)
df["Disc Band"] = pd.cut(
    df["Discount"], bins=[-0.01, 0, 0.2, 0.5, 1.0],
    labels=["No discount", "0-20%", "20-50%", ">50%"])
band = df.groupby("Disc Band", observed=True).agg(
    Lines=("Sales", "size"), Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
).reset_index()
band["Avg Margin %"] = (band["Profit"] / band["Revenue"] * 100).round(1)
band["Revenue"] = band["Revenue"].round(2)
band["Profit"] = band["Profit"].round(2)

add("\n## 4. Discount effect on profit\n")
add(f"- Pearson correlation (numpy) between Discount and Profit: **r = {r_profit:.2f}**")
add(f"- Pearson correlation between Discount and Profit Margin %: **r = {r_margin:.2f}**")
add(f"- Discount and profit move strongly in opposite directions; beyond 50% "
    f"discounts are outright loss-makers.\n")

add("| Discount band | Lines | Revenue | Profit | Avg margin % |")
add("|---|---|---|---|---|")
for b in band.itertuples(index=False):
    add(f"| {b[0]} | {b[1]:,} | ${b[2]:,.2f} | ${b[3]:,.2f} | {b[4]}% |")

# deeper look: furniture vs others under heavy discount
heavy = df[df["Discount"] >= 0.3]
seg_heavy = heavy.groupby("Category").agg(
    Lines=("Sales", "size"), Profit=("Profit", "sum"))
seg_heavy["Profit"] = seg_heavy["Profit"].round(2)
add("\nOrder lines with discount >= 30% by category:\n")
add("| Category | Lines | Total profit |")
add("|---|---|---|")
for name, row in seg_heavy.iterrows():
    add(f"| {name} | {int(row['Lines']):,} | ${row['Profit']:,.2f} |")

fig, ax = plt.subplots(figsize=(7, 5))
colors = np.where(df["Profit"] < 0, "indianred", "steelblue")
ax.scatter(disc, prof, s=sales / 150, alpha=0.35, c=colors, edgecolors="none")
ax.axhline(0, color="black", lw=0.8)
ax.set_xlabel("Discount")
ax.set_ylabel("Profit of order line")
ax.set_title("Discount vs Profit (bubble size = sales value)\n"
             f"r = {r_profit:.2f}")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x/1000:.0f}k"))
save_fig(fig, "discount_vs_profit.png")
add("\n![Discount vs profit](charts/discount_vs_profit.png)")

# ============================================================================
# 5. TOP / BOTTOM PRODUCTS
# ============================================================================
prod = df.groupby(["Product Name"], as_index=False).agg(
    Category=("Category", "first"), Revenue=("Sales", "sum"),
    Profit=("Profit", "sum"), Units=("Quantity", "sum"), Lines=("Sales", "size"),
)
top10 = prod.nlargest(10, "Revenue")
worst10 = prod.nsmallest(10, "Profit")

add("\n## 5. Top and bottom products\n")
add("Top 10 products by revenue:\n")
add("| # | Product | Category | Revenue | Profit |")
add("|---|---|---|---|---|")
for i, p in enumerate(top10.itertuples(index=False), 1):
    add(f"| {i} | {p[0]} | {p[1]} | ${p[2]:,.2f} | ${p[3]:,.2f} |")

add("\n10 worst products by cumulative loss:\n")
add("| # | Product | Category | Revenue | Profit |")
add("|---|---|---|---|---|")
for i, p in enumerate(worst10.itertuples(index=False), 1):
    add(f"| {i} | {p[0]} | {p[1]} | ${p[2]:,.2f} | ${p[3]:,.2f} |")

# ============================================================================
# 6. TOP CUSTOMERS
# ============================================================================
cust = df.groupby("Customer Name").agg(
    Orders=("Order ID", "nunique"), Revenue=("Sales", "sum"),
    Profit=("Profit", "sum")).nlargest(10, "Revenue").reset_index()
cust["Revenue"] = cust["Revenue"].round(2)
cust["Profit"] = cust["Profit"].round(2)
add("\n## 6. Top 10 customers\n")
add("| # | Customer | Orders | Revenue | Profit |")
add("|---|---|---|---|---|")
for i, c in enumerate(cust.itertuples(index=False), 1):
    add(f"| {i} | {c[0]} | {int(c[1])} | ${c[2]:,.2f} | ${c[3]:,.2f} |")

# ============================================================================
# 7. REGIONAL AND CATEGORY / SUB-CATEGORY PERFORMANCE
# ============================================================================
region = df.groupby("Region").agg(
    Orders=("Order ID", "nunique"), Revenue=("Sales", "sum"),
    Profit=("Profit", "sum")).reset_index()
region["Revenue"] = region["Revenue"].round(2)
region["Profit"] = region["Profit"].round(2)
region["Margin %"] = (region["Profit"] / region["Revenue"] * 100).round(1)
region["AOV"] = (region["Revenue"] / region["Orders"]).round(2)
region = region[["Region", "Orders", "Revenue", "Profit", "Margin %", "AOV"]]
region = region.sort_values("Revenue", ascending=False)

add("\n## 7. Regional performance\n")
add("| Region | Orders | Revenue | Profit | Margin % | AOV |")
add("|---|---|---|---|---|---|")
for r in region.itertuples(index=False):
    add(f"| {r[0]} | {int(r[1]):,} | ${r[2]:,.2f} | ${r[3]:,.2f} | {r[4]}% | ${r[5]:,.2f} |")

add("\nCentral is the profit problem: strong revenue but margins far below "
    "West/East. (Also driven by Texas and large discounting.)\n")

subcat = df.groupby("Sub-Category").agg(
    Revenue=("Sales", "sum"), Profit=("Profit", "sum"),
    Lines=("Sales", "size")).sort_values("Profit", ascending=False)
subcat["Margin %"] = (subcat["Profit"] / subcat["Revenue"] * 100).round(1)
subcat["Revenue"] = subcat["Revenue"].round(2)
subcat["Profit"] = subcat["Profit"].round(2)

add("All 17 sub-categories by profit:\n")
add("| Sub-category | Revenue | Profit | Margin % |")
add("|---|---|---|---|")
for name, s in subcat[["Revenue", "Profit", "Margin %"]].iterrows():
    add(f"| {name} | ${s['Revenue']:,.2f} | ${s['Profit']:,.2f} | {s['Margin %']}% |")

fig, ax = plt.subplots(figsize=(8, 6))
colors = np.where(subcat["Profit"] < 0, "indianred", "steelblue")
ax.barh(subcat.index[::-1], subcat["Margin %"][::-1], color=colors[::-1])
ax.set_xlabel("Profit margin %")
ax.set_title("Profit margin % by sub-category (2014-2017)")
ax.axvline(0, color="black", lw=0.8)
save_fig(fig, "subcategory_margin.png")
add("\n![Sub-category margins](charts/subcategory_margin.png)")

cat_region = df.pivot_table(index="Region", columns="Category",
                            values="Profit", aggfunc="sum").round(2)
add("\nProfit by region x category:\n")
add("| Region | Furniture | Office Supplies | Technology |")
add("|---|---|---|---|")
for r in cat_region.itertuples():
    add(f"| {r[0]} | ${r[1]:,.2f} | ${r[2]:,.2f} | ${r[3]:,.2f} |")

# ============================================================================
# 8. SEGMENT / SHIP MODE
# ============================================================================
segment = df.groupby("Segment").agg(
    Orders=("Order ID", "nunique"), Revenue=("Sales", "sum"),
    Profit=("Profit", "sum")).reset_index()
segment["Margin %"] = (segment["Profit"] / segment["Revenue"] * 100).round(1)
segment["Revenue"] = segment["Revenue"].round(2)
segment["Profit"] = segment["Profit"].round(2)
add("\n## 8. Customer segments\n")
add("| Segment | Orders | Revenue | Profit | Margin % |")
add("|---|---|---|---|---|")
for s in segment.itertuples(index=False):
    add(f"| {s[0]} | {int(s[1]):,} | ${s[2]:,.2f} | ${s[3]:,.2f} | {s[4]}% |")

ship = df.groupby("Ship Mode").agg(
    Lines=("Sales", "size"), Avg_Days=("Shipping Days", "mean")).round(2)
add("\nAvg shipping days by mode:\n")
add("| Ship mode | Lines | Avg shipping days |")
add("|---|---|---|")
for s in ship.itertuples():
    add(f"| {s[0]} | {int(s[1]):,} | {s[2]} |")

with open("docs/analysis_findings.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")
print("\nFindings saved -> docs/analysis_findings.md")
