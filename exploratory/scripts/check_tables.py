#Check if FAERS and MEDICARE tables actually loaded correctly into the database

import sqlite3

# Connect to the database in the data directory

conn = sqlite3.connect('data/faers+medicare.db') ## Change to match where your database is

#===== DON'T CHANGE ANYTHING BELOW THIS LINE
cursor = conn.cursor()
# Check available tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Available tables:")
for table in tables:
    if table[0].endswith(('q1','q2','q3','q4','d_2023')):
        print(f"Raw Table - {table[0]}")
    else:
        print(f"Cleaned Table - {table[0]}")

conn.close()

# If terminal says "Available tables: ", and nothing is listed, then check if it was loaded to the correct area.
# This is what you should see in terminal after first loading up the database:
# Available tables:
# - Raw Table - faers_demo_2023q1
# - Raw Table - faers_demo_2023q2
# - Raw Table - faers_demo_2023q3
# - Raw Table - faers_demo_2023q4
# - Raw Table - faers_drug_2023q1
# - Raw Table - faers_drug_2023q2
# - Raw Table - faers_drug_2023q3
# - Raw Table - faers_drug_2023q4
# - Raw Table - faers_indi_2023q1
# - Raw Table - faers_indi_2023q2
# - Raw Table - faers_indi_2023q3
# - Raw Table - faers_indi_2023q4
# - Raw Table - faers_outc_2023q1
# - Raw Table - faers_outc_2023q2
# - Raw Table - faers_outc_2023q3
# - Raw Table - faers_outc_2023q4
# - Raw Table - faers_reac_2023q1
# - Raw Table - faers_reac_2023q2
# - Raw Table - faers_reac_2023q3
# - Raw Table - faers_reac_2023q4
# - Raw Table - medicare_part_d_2023

#  After steps 0 through 8b, run this script again and you
# should now see the following tables added: 
# - Cleaned Table - faers_demo_2023_latest_us
# - Cleaned Table - faers_drug_2023_ps
# - Cleaned Table - faers_reac_2023_keep
# - Cleaned Table - faers_outc_2023_flags
# - Cleaned Table - faers_indi_2023_keep
