import sqlite3

# IMPORTANT: update this path if your DB file is in a different folder
conn = sqlite3.connect("database/database.db")
cur = conn.cursor()

# Add missing columns
try:
    cur.execute("ALTER TABLE Tenant ADD COLUMN apartment_type VARCHAR(50);")
    print("Added apartment_type")
except Exception as e:
    print("apartment_type already exists:", e)

try:
    cur.execute("ALTER TABLE Tenant ADD COLUMN lease_period VARCHAR(50);")
    print("Added lease_period")
except Exception as e:
    print("lease_period already exists:", e)

try:
    cur.execute("ALTER TABLE Tenant_Reference ADD COLUMN reference_email VARCHAR(255);")
    print("Added reference_email")
except Exception as e:
    print("reference_email already exists:", e)

conn.commit()
conn.close()

print("Database patch complete!")
