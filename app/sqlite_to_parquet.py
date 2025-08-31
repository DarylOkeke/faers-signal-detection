import duckdb
import pandas as pd
import os
from pathlib import Path

# Read from DuckDB and save as Parquet
DB_PATH = "data/faers+medicare.duckdb"

if not os.path.exists(DB_PATH):
    print(f"Error: Database not found: {DB_PATH}")
    print("Please ensure the DuckDB database exists before running this script.")
    exit(1)

print("Connecting to DuckDB database...")
con = duckdb.connect(DB_PATH)
print("Exporting v_anydrug_signal_2x2_2023...")
df = con.execute("""
    SELECT ingredient_std, reaction_pt, a, b, c, d
    FROM v_anydrug_signal_2x2_2023
""").df()
con.close()

print(f"Loaded {len(df):,} rows from DuckDB")
print("Sample data:")
print(df.head())

# Save directly as Parquet
parquet_path = "data/anydrug_2023.parquet"
df.to_parquet(parquet_path, compression='snappy')
print(f"✓ Successfully created {parquet_path} with {len(df):,} rows")

# Verify with DuckDB
print("Verifying Parquet file...")
con = duckdb.connect()
n = con.execute(f"SELECT COUNT(*) FROM '{parquet_path}'").fetchone()[0]
print(f"✓ Verification successful: {n:,} rows in Parquet file")
con.close()
