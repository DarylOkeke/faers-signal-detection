# Load FAERS Quarterly Data and Medicare Part D Yearly data using DuckDB
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vendor"))

from pathlib import Path
import duckdb
import re
import time

print("Loading FAERS and Medicare data into DuckDB database...")

# ==== CONFIG ====
DATA_DIR = Path("./data")
DB_PATH = Path("./data/faers+medicare.duckdb")

TABLES = ["DEMO", "DRUG", "REAC", "OUTC", "INDI"]
ONLY_YEARS = None  # e.g. {2023, 2024} to restrict; or None for all

# ==============================
def parse_faers_filename(path: Path):
    m = re.match(r"(?i)^(DEMO|DRUG|REAC|OUTC|INDI)(\d{2})(Q[1-4])\.txt$", path.name)
    if not m:
        return None
    tbl, yy, q = m.groups()
    year = 2000 + int(yy)
    return tbl.upper(), year, q.upper()

def discover_faers_ascii_files(base: Path):
    patterns = ["**/faers_ascii_*/*ASCII*", "**/FAERSQ[1-4]_*/*ASCII*"]
    for pattern in patterns:
        for ascii_dir in base.glob(pattern):
            for p in ascii_dir.glob("*.txt"):
                parsed = parse_faers_filename(p)
                if parsed:
                    yield (*parsed, p)

def load_faers(con):
    files = sorted(discover_faers_ascii_files(DATA_DIR))
    if not files:
        print("No FAERS ASCII files discovered. Check DATA_DIR.")
        return
    for tbl, year, q, path in files:
        start_time = time.time()
        quarter_label = f"{year}{q}"
        sql_table = f"faers_{tbl.lower()}_{quarter_label.lower()}"
        try:
            con.execute(f"""
                CREATE OR REPLACE TABLE {sql_table} AS
                SELECT *, '{quarter_label}' AS quarter
                FROM read_csv_auto('{path.as_posix()}', delim='$', header=TRUE, ignore_errors=TRUE);
            """)
            elapsed = time.time() - start_time
            count = con.execute(f"SELECT COUNT(*) FROM {sql_table}").fetchone()[0]
            print(f"[OK] {sql_table:28s} <- {path.name:16s} rows={count:,} ({elapsed:.1f}s)")
        except Exception as e:
            print(f"[SKIP] {path} -> error: {e}")
            continue

def find_latest_medicare_file(base: Path, year=2023):
    yy = f"{year % 100:02d}"
    pattern_csv  = f"**/MUP_DPR_*DY{yy}_NPIBN.csv"
    pattern_xlsx = f"**/MUP_DPR_*DY{yy}_NPIBN.xlsx"
    candidates = list(base.glob(pattern_csv)) + list(base.glob(pattern_xlsx))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)

def load_medicare(con, year=2023):
    p = find_latest_medicare_file(DATA_DIR, year=year)
    if not p:
        print(f"[INFO] No Medicare file found for DY{year%100:02d}")
        return False
    print(f"[INFO] Loading Medicare Part D from: {p}")
    start_time = time.time()
    table_name = f"medicare_part_d_{year}"
    try:
        if p.suffix.lower() == ".csv":
            con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{p.as_posix()}', header=TRUE, ignore_errors=TRUE);
            """)
        else:
            con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_excel('{p.as_posix()}');
            """)
        elapsed = time.time() - start_time
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"[OK] {table_name} rows={count:,} ({elapsed:.1f}s)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load Medicare: {e}")
        return False

def main():
    print(f"Creating DuckDB database at: {DB_PATH.resolve()}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    print("Loading FAERS data...")
    load_faers(con)
    print("Loading Medicare data...")
    load_medicare(con, year=2023)
    con.close()
    print("Database loading complete!")

if __name__ == "__main__":
    main()
