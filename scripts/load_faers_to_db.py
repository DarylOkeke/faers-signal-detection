import pandas as pd
import sqlite3
import os

# 1. Configuration – adjust QUARTERS if you only want one
DATA_DIR = '../data'
QUARTERS = ['24Q4', '25Q1']      # or ['25Q1'] to just load Q1 2025
TABLES = ['DEMO', 'DRUG', 'REAC']
DB_PATH = os.path.join(DATA_DIR, 'faers.db')

# 2. Connect to your SQLite DB
conn = sqlite3.connect(DB_PATH)

# 3. Loop through quarters and tables
for quarter in QUARTERS:
    year = 2000 + int(quarter[:2])        # e.g. 2000+24 = 2024
    period = quarter[2:]                  # 'Q4' or 'Q1'
    folder = f"FAERS{period}_{year}"      # e.g. 'FAERSQ4_2024'
    
    for tbl in TABLES:
        path = os.path.join(DATA_DIR, folder, 'ASCII', f"{tbl}{quarter}.txt")
        
        # 4. Read the raw file into pandas
        df = pd.read_csv(
            path,
            sep='$',
            encoding='latin-1',
            dtype=str,
            low_memory=False
        )
        
        # 5. Tag rows with their quarter
        df['quarter'] = quarter
        
        # 6. Write to SQLite
        table_name = f"{tbl.lower()}{quarter.lower()}"
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # print(f"Loaded {table_name}: {df.shape[0]} rows")

# 7. Close connection
conn.close()
