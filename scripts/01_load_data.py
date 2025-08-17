
#IMPORTANT NOTES BEFORE RUNNING

#Load FAERS Quarterly Data and Medicare Part D Yearly data.
#Before running this script, make sure you have installed everything in the requirements.txt file.
#Also make sure that you have downloaded the necessary data files and put them in a 'data' folder(Change DATA_DIR if needed).
#Lastly, DO NOT CHANGE THE NAMES OF THE FAERS ASCII FILES OR THE MEDICARE CSV FILES. LEAVE THEM AS THE NAME THAT IT COMES WITH ON DOWNLOAD.


from pathlib import Path
import pandas as pd
import sqlite3
import re
import time

print("Loading FAERS and Medicare data into SQLite database...")

# ==== CONFIG YOU MAY TWEAK ====

# Path to the folder containing your FAERS and Medicare data.
# Change this if your 'data' folder is in a different location relative to this script.
# Example: Path("../data") if the data folder is one level up from the script.
DATA_DIR = Path("./data")

# Path (and filename) for the SQLite database that will be created or updated.
# Change the filename if you want to keep multiple versions, or set a full path to save elsewhere.
# Example: Path("../faers+medicare.db") to save in the parent directory of the script.
DB_PATH  = Path("./faers+medicare.db") 

TABLES   = ["DEMO", "DRUG", "REAC", "OUTC", "INDI"]     # FAERS ASCII tables to ingest

ONLY_YEARS = None       # e.g. {2023, 2024} to restrict; or None for all

# DO NOT CHANGE ANYTHING BELOW THIS LINE
# UNLESS YOU FULLY UNDERSTAND THE ETL PIPELINE.
# The functions below handle standardized column cleaning,
# file discovery for multiple FAERS folder formats, and data loading.
# Changing these could break reproducibility across machines.
# ==========================================================


def clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
          .str.strip()
          .str.replace(r"\s+", "_", regex=True)
          .str.replace(r"[^A-Za-z0-9_]", "", regex=True)
    )
    return df


def parse_faers_filename(path: Path):
    """
    Accepts names like DRUG23Q1.txt, reac24q3.txt, OUTC25Q4.TXT (case-insensitive).
    Returns: table(upper), year(YYYY int), quarter('Q1'..'Q4').
    """
    m = re.match(r"(?i)^(DEMO|DRUG|REAC|OUTC|INDI)(\d{2})(Q[1-4])\.txt$", path.name)
    if not m:
        return None
    tbl, yy, q = m.groups()
    year = 2000 + int(yy)  # FAERS 20xx
    return tbl.upper(), year, q.upper()

# Discover FAERS ASCII files
print("Looking for FAERS ASCII files under:", DATA_DIR.resolve())

def discover_faers_ascii_files(base: Path):
    """
    Finds all FAERS ASCII files under folders like:
    - faers_ascii_2023q1/ASCII/*.txt
    - FAERSQ1_2023/ASCII/*.txt
    regardless of capitalization.
    """
    patterns = [
        "**/faers_ascii_*/*ASCII*",
        "**/FAERSQ[1-4]_*/*ASCII*"
    ]
    
    for pattern in patterns:
        for ascii_dir in base.glob(pattern):
            for p in ascii_dir.glob("*.txt"):
                parsed = parse_faers_filename(p)
                if parsed:
                    yield (*parsed, p)



def load_faers(conn):
    # Enable performance optimizations
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 1000000")
    conn.execute("PRAGMA temp_store = memory")
    
    files = sorted(discover_faers_ascii_files(DATA_DIR))
    if not files:
        print("No FAERS ASCII files discovered. Check DATA_DIR.")
        return

    # Track what we actually loaded
    seen = set()
    for tbl, year, q, path in files:
        start_time = time.time()
        quarter_label = f"{year}{q}"          # e.g., 2023Q1
        sql_table = f"faers_{tbl.lower()}_{quarter_label.lower()}"
        seen.add((tbl, quarter_label))

        try:
            # Read file in smaller chunks to avoid SQLite limits
            chunk_size = 10000  # Smaller chunks to avoid SQL variable limits
            first_chunk = True
            total_rows = 0
            
            for chunk in pd.read_csv(
                path,
                sep="$",
                encoding="latin-1",
                dtype=str,
                low_memory=False,
                chunksize=chunk_size
            ):
                chunk["quarter"] = quarter_label
                chunk = clean_cols(chunk)
                
                # Use replace for first chunk, append for subsequent chunks
                if_exists = "replace" if first_chunk else "append"
                chunk.to_sql(sql_table, conn, if_exists=if_exists, index=False)
                
                first_chunk = False
                total_rows += len(chunk)
            
            elapsed = time.time() - start_time
            print(f"[OK] {sql_table:28s} <- {path.name:16s} rows={total_rows:,} ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"[SKIP] {path} -> read error: {e}")
            continue

    # Report missing tables per quarter (helps QA)
    by_q = {}
    for tbl, q in seen:
        by_q.setdefault(q, set()).add(tbl)
    for q, got in sorted(by_q.items()):
        missing = set(TABLES) - got
        if missing:
            print(f"[WARN] {q} missing tables: {sorted(missing)}")

print("Looking for Medicare files under:", DATA_DIR.resolve())
for p in DATA_DIR.rglob("*MUP_DPR*"):
    print("Found candidate:", p)

def find_latest_medicare_file(base: Path, year=2023):
    """
    Finds the newest Medicare Part D prescriber file for DY{yy} in CSV or XLSX anywhere under DATA_DIR.
    Matches names like:
      MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv / .xlsx
    Returns Path or None.
    """
    yy = f"{year % 100:02d}"
    pattern_csv  = f"**/MUP_DPR_*DY{yy}_NPIBN.csv"
    pattern_xlsx = f"**/MUP_DPR_*DY{yy}_NPIBN.xlsx"

    candidates = list(base.glob(pattern_csv)) + list(base.glob(pattern_xlsx))
    if not candidates:
        return None
    # pick the most recently modified
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_medicare(conn, year=2023):
    # Enable performance optimizations for Medicare loading
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 1000000")
    conn.execute("PRAGMA temp_store = memory")
    
    p = find_latest_medicare_file(DATA_DIR, year=year)
    if not p:
        print(f"[INFO] No Medicare Part D file for DY{year%100:02d} found under {DATA_DIR}")
        return False

    print(f"[INFO] Loading Medicare Part D from: {p}")
    start_time = time.time()
    
    try:
        table_name = f"medicare_part_d_{year}"
        
        if p.suffix.lower() == ".csv":
            # Use chunking for large CSV files to avoid memory and SQL variable limits
            chunk_size = 50000  # Smaller chunks to avoid SQL limits
            first_chunk = True
            total_rows = 0
            
            print(f"[INFO] Reading CSV in chunks of {chunk_size:,} rows...")
            
            for i, chunk in enumerate(pd.read_csv(p, dtype=str, low_memory=False, chunksize=chunk_size)):
                chunk = clean_cols(chunk)
                
                # Use replace for first chunk, append for subsequent chunks
                if_exists = "replace" if first_chunk else "append"
                chunk.to_sql(table_name, conn, if_exists=if_exists, index=False)
                
                first_chunk = False
                total_rows += len(chunk)
                
                if (i + 1) % 10 == 0:  # Progress update every 10 chunks
                    print(f"[INFO] Processed {total_rows:,} rows...")
            
        else:
            # For Excel files, read directly (usually smaller)
            print(f"[INFO] Reading Excel file...")
            df = pd.read_excel(p, dtype=str)
            df = clean_cols(df)
            total_rows = len(df)
            
            print(f"[INFO] Writing {total_rows:,} rows to database...")
            df.to_sql(table_name, conn, if_exists="replace", index=False)

        elapsed = time.time() - start_time
        print(f"[OK] {table_name} rows={total_rows:,} ({elapsed:.1f}s)")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load Medicare data: {e}")
        return False


def main():
    print(f"Creating database at: {DB_PATH.resolve()}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Use connection with optimizations
    with sqlite3.connect(DB_PATH, timeout=30.0) as conn:
        # Global performance settings
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL") 
        conn.execute("PRAGMA cache_size = 1000000")
        conn.execute("PRAGMA temp_store = memory")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
        
        print("Loading FAERS data...")
        load_faers(conn)
        
        print("Loading Medicare data...")
        load_medicare(conn, year=2023)
        
        print("Database loading complete!")


if __name__ == "__main__":
    main()
