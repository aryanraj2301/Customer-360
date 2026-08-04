import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "warehouse", "customer360.duckdb")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

con = duckdb.connect(DB_PATH)
con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

tables = ["customers", "orders", "order_items", "support_tickets", "web_events"]
for t in tables:
    csv_path = os.path.join(os.path.dirname(__file__), f"{t}.csv")
    con.execute(f"""
        CREATE OR REPLACE TABLE bronze.{t} AS
        SELECT * FROM read_csv_auto('{csv_path}')
    """)
    count = con.execute(f"SELECT COUNT(*) FROM bronze.{t}").fetchone()[0]
    print(f"bronze.{t}: {count} rows loaded")

con.close()