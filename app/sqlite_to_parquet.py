import sqlite3
import pandas as pd

# Read from SQLite and save as CSV first
DB_PATH = "data/faers+medicare.db"

print("Connecting to SQLite database...")
with sqlite3.connect(DB_PATH) as conn:
    print("Exporting v_anydrug_signal_2x2_2023...")
    df = pd.read_sql_query("""
        SELECT ingredient_std, reaction_pt, a, b, c, d
        FROM v_anydrug_signal_2x2_2023
    """, conn)

print(f"Loaded {len(df):,} rows from SQLite")
print("Sample data:")
print(df.head())

# Save as CSV first
csv_path = "data/anydrug_2023.csv"
df.to_csv(csv_path, index=False)
print(f"Saved to {csv_path}")

# Now convert to Parquet using DuckDB
import duckdb
con = duckdb.connect()
print("Converting CSV to Parquet...")
con.execute(f"""
    COPY (SELECT * FROM '{csv_path}')
    TO 'data/anydrug_2023.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD);
""")

# Verify
n = con.execute("SELECT COUNT(*) FROM 'data/anydrug_2023.parquet'").fetchone()[0]
print(f"✓ Successfully created data/anydrug_2023.parquet with {n:,} rows")

# Clean up CSV
import os
os.remove(csv_path)
print("✓ Cleaned up temporary CSV file")
