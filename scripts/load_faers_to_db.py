import pandas as pd
import sqlite3
import os

# 1. Configuration – adjust QUARTERS if you only want one
DATA_DIR = '../data'
QUARTERS = ['24Q4', '25Q1']      # or ['25Q1'] to just load Q1 2025
TABLES = ['DEMO', 'DRUG', 'REAC', 'OUTC', 'INDI']
DB_PATH = os.path.join(DATA_DIR, 'faers.db')

def load_medicare_data(conn):
    """Load Medicare Part D data into SQLite database"""
    # Path to the extracted Medicare data
    medicare_dir = os.path.join(DATA_DIR, 'Medicare_Part_D_Extracted', 
                               'Medicare Part D Prescribers - by Provider and Drug', '2023')
    
    csv_file = 'MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv'
    csv_path = os.path.join(medicare_dir, csv_file)
    
    if os.path.exists(csv_path):
        print(f"Loading Medicare Part D data from {csv_path}...")
        
        # Read CSV file
        df = pd.read_csv(
            csv_path,
            dtype=str,  # Read all columns as strings to avoid data type issues
            low_memory=False
        )
        
        print(f"Loaded {df.shape[0]:,} rows with {df.shape[1]} columns")
        
        # Clean column names (remove spaces and special characters for SQL compatibility)
        df.columns = df.columns.str.replace(' ', '_').str.replace('[^A-Za-z0-9_]', '', regex=True)
        
        # Load into SQLite
        table_name = 'medicare_part_d_2023'
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        print(f"Successfully loaded data into table: {table_name}")
        return True
    else:
        print(f"Medicare data file not found: {csv_path}")
        return False

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

# 8. Load Medicare Part D data
load_medicare_data(conn)

# 9. Close connection
conn.close()
