import sqlite3

DB_FILE = "blog.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("Starting users table migration...")

# =========================================================
# CHECK CURRENT USERS TABLE
# =========================================================

columns = cursor.execute(
    "PRAGMA table_info(users)"
).fetchall()

column_names = [column[1] for column in columns]

print("\nCurrent users table structure:")
for column in columns:
    print(column)


# =========================================================
# ADD PROVIDER COLUMN
# =========================================================

if "provider" not in column_names:

    print("\nAdding provider column...")

    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN provider VARCHAR(50)
    """)

    conn.commit()

    print("Provider column added successfully!")

else:

    print("\nProvider column already exists.")


# =========================================================
# VERIFY TABLE
# =========================================================

result = cursor.execute(
    "PRAGMA table_info(users)"
).fetchall()

print("\nUpdated users table structure:")

for column in result:
    print(column)


# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()

print("\nMigration completed successfully!")