import sqlite3
import os

# Connect to database
# Determine the database path relative to this file. This allows the script to
# be executed from any working directory.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(ROOT_DIR, 'data', 'faers.db')
# SQL directory relative to the project root
SQL_DIR = os.path.join(ROOT_DIR, 'sql_queries')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Running all queries in sequence...\n")

# Query 1: FAERS adverse event counts
print("1. Creating FAERS adverse event counts table...")
try:
    with open(os.path.join(SQL_DIR, 'dupixent_vs_adbry.sql'), 'r') as f:
        query1 = f.read()
    cursor.executescript(query1)
    
    # Show results
    cursor.execute("SELECT * FROM faers_dupixent_adbry_counts ORDER BY drug_name, quarter")
    results1 = cursor.fetchall()
    print("FAERS Adverse Event Counts Created:")
    print("Drug Name | Quarter | Report Count")
    print("-" * 35)
    for row in results1:
        print(f"{row[0]:<9} | {row[1]:<7} | {row[2]:,}")
    print()
    
except Exception as e:
    print(f"Error in query 1: {e}")
    print()

# Query 2: Medicare prescription counts  
print("2. Creating Medicare prescription counts table...")
try:
    with open(os.path.join(SQL_DIR, 'prescriptionct_dupixent_vs_adbry.sql'), 'r') as f:
        query2 = f.read()
    cursor.executescript(query2)
    
    # Show results
    cursor.execute("SELECT * FROM medicare_dupixent_adbry_prescriptions ORDER BY drug_name")
    results2 = cursor.fetchall()
    print("Medicare Prescription Data Created:")
    print("Drug Name | Generic Name | Claims | 30-Day Fills | Beneficiaries")
    print("-" * 65)
    for row in results2:
        print(f"{row[0]:<9} | {row[1]:<12} | {row[3]:,} | {row[4]:,} | {row[5]:,}")
    print()
    
except Exception as e:
    print(f"Error in query 2: {e}")
    print()

# Query 3: Normalized analysis
print("3. Creating normalized adverse event analysis...")
try:
    with open(os.path.join(SQL_DIR, 'normalized_ae_analysis.sql'), 'r') as f:
        query3 = f.read()
    cursor.executescript(query3)
    
    # Show results
    cursor.execute("SELECT * FROM normalized_ae_rates_dupixent_adbry ORDER BY drug_name")
    results3 = cursor.fetchall()
    print("Normalized Adverse Event Analysis Created:")
    print("Drug Name | FAERS Reports | Medicare Claims | AE per 1000 Claims | AE per 1000 Beneficiaries")
    print("-" * 90)
    for row in results3:
        claims_str = f"{row[2]:,}" if row[2] is not None else "N/A"
        ae_claims_str = f"{row[6]}" if row[6] is not None else "N/A"  
        ae_benes_str = f"{row[7]}" if row[7] is not None else "N/A"
        faers_str = f"{row[1]:,}" if row[1] is not None else "N/A"
        print(f"{row[0]:<25} | {faers_str:<13} | {claims_str:<15} | {ae_claims_str:<18} | {ae_benes_str}")
    print()
    
except Exception as e:
    print(f"Error in query 3: {e}")
    print()

print("All queries completed!")
conn.close()
