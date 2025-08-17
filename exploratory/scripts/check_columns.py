# Enter the table you want to check the columns for:
table=input("Enter table name: ")
import sqlite3

# Connect to the database in the data directory

conn = sqlite3.connect('data/faers+medicare.db') ## Change to match where your database is

# Check the columns in the specified table
cursor = conn.cursor()
cursor.execute(f"PRAGMA table_info({table})")
columns = cursor.fetchall()

print(f"Columns in table '{table}':")
for column in columns:
    print(f" - {column[1]}")

conn.close()