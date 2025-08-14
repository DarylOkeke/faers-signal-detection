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
    print(f"- {table[0]}")

conn.close()

# If terminal says "Available tables: ", and nothing is listed, then check if it was loaded to the correct area.
# This is what you should see in terminal:
# Available tables:
# - faers_demo_2023q1
# - faers_demo_2023q2
# - faers_demo_2023q3
# - faers_demo_2023q4
# - faers_drug_2023q1
# - faers_drug_2023q2
# - faers_drug_2023q3
# - faers_drug_2023q4
# - faers_indi_2023q1
# - faers_indi_2023q2
# - faers_indi_2023q3
# - faers_indi_2023q4
# - faers_outc_2023q1
# - faers_outc_2023q2
# - faers_outc_2023q3
# - faers_outc_2023q4
# - faers_reac_2023q1
# - faers_reac_2023q2
# - faers_reac_2023q3
# - faers_reac_2023q4
# - medicare_part_d_2023