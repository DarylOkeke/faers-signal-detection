## Had to do 
import sqlite3
import os

# Connect to database
conn = sqlite3.connect(os.path.join('..', 'data', 'faers.db'))
cursor = conn.cursor()

print("Searching for Dupixent/dupilumab variants...")
cursor.execute("SELECT DISTINCT Gnrc_Name FROM medicare_part_d_2023 WHERE Gnrc_Name LIKE '%dupil%' OR Brnd_Name LIKE '%dupix%' LIMIT 10")
results = cursor.fetchall()
print("Generic names found:")
for row in results:
    print(f"  {row[0]}")

cursor.execute("SELECT DISTINCT Brnd_Name FROM medicare_part_d_2023 WHERE Gnrc_Name LIKE '%dupil%' OR Brnd_Name LIKE '%dupix%' LIMIT 10")
results = cursor.fetchall()
print("Brand names found:")
for row in results:
    print(f"  {row[0]}")

print("\nSearching for Adbry/tralokinumab variants...")
cursor.execute("SELECT DISTINCT Gnrc_Name FROM medicare_part_d_2023 WHERE Gnrc_Name LIKE '%tralo%' OR Brnd_Name LIKE '%adbr%' LIMIT 10")
results = cursor.fetchall()
print("Generic names found:")
for row in results:
    print(f"  {row[0]}")

cursor.execute("SELECT DISTINCT Brnd_Name FROM medicare_part_d_2023 WHERE Gnrc_Name LIKE '%tralo%' OR Brnd_Name LIKE '%adbr%' LIMIT 10")
results = cursor.fetchall()
print("Brand names found:")
for row in results:
    print(f"  {row[0]}")

# Let's also try broader searches
print("\nBroader search for any drug names containing key parts...")
cursor.execute("SELECT DISTINCT Gnrc_Name, Brnd_Name FROM medicare_part_d_2023 WHERE Gnrc_Name LIKE '%mab%' AND (Gnrc_Name LIKE '%dup%' OR Gnrc_Name LIKE '%tral%') LIMIT 10")
results = cursor.fetchall()
print("Monoclonal antibodies with dup/tral:")
for row in results:
    print(f"  Generic: {row[0]}, Brand: {row[1]}")

conn.close()
