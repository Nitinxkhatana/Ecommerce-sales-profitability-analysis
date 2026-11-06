"""
Stage 3 - Run all analysis queries in sql/analysis_queries.sql against
data/ecommerce.db and save a formatted report to docs/sql_results.md.

Each SQL section block (starting with a comment header '-- Q<n>') is executed
separately. Results are printed to console and written to markdown.
"""

import re
import sqlite3
import pandas as pd

DB_PATH = "data/ecommerce.db"
SQL_PATH = "sql/analysis_queries.sql"
OUT_PATH = "docs/sql_results.md"


def load_queries(path):
    """Split the SQL file into labeled queries (comment header + statement)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # keep only comment/SQL content before any next marker
    pattern = re.compile(r"-- (Q\d+ .+?)\n(.*?)(?=-- Q\d+ |\Z)", re.DOTALL)
    queries = []
    for m in pattern.finditer(text):
        label = m.group(1).strip()
        sql = m.group(2).strip()
        # stop at the next section banner (==== line) if present at block start
        queries.append((label, sql))
    return queries


def main():
    conn = sqlite3.connect(DB_PATH)
    queries = load_queries(SQL_PATH)
    report = [
        "# SQL Analysis Results",
        "",
        "Database: `data/ecommerce.db` | Table: `superstore` (9,993 rows) |",
        "All numbers are computed by SQLite from the cleaned Superstore data.",
        "",
    ]
    for label, sql in queries:
        title = label.split(":", 1)[0]
        desc = label.split(":", 1)[1].strip()
        df = pd.read_sql_query(sql, conn)
        print(f"\n=== {title} ===")
        print(df.to_string(index=False))
        report.append(f"## {title}")
        report.append(f"{desc}\n")
        report.append("```")
        report.append(df.to_string(index=False))
        report.append("```\n")
    conn.close()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"\nReport saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
