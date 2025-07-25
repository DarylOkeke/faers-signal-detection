import pandas as pd
import sqlite3
import os

def load_medicare_data():
    """Load Medicare Part D data into SQLite database"""
    
    # Configuration
    DATA_DIR = '../data'
    DB_PATH = os.path.join(DATA_DIR, 'faers.db')
    
    # Path to the extracted Medicare data
    medicare_dir = os.path.join(DATA_DIR, 'Medicare_Part_D_Extracted', 
                               'Medicare Part D Prescribers - by Provider and Drug', '2023')
    
    csv_file = 'MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv'
    csv_path = os.path.join(medicare_dir, csv_file)
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    
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
    
    # Close connection
    conn.close()
    
    return table_name, df.shape[0]

if __name__ == "__main__":
    table_name, row_count = load_medicare_data()
    print(f"Medicare data loaded: {table_name} with {row_count:,} rows")
