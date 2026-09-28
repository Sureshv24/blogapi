import sqlite3

DB_FILE = "blog.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("Starting posts table migration...")

# =========================================================
# CHECK CURRENT POSTS TABLE
# =========================================================

columns = cursor.execute(
    "PRAGMA table_info(posts)"
).fetchall()

print("\nCurrent posts table structure:")

for column in columns:
    print(column)


existing_columns = {
    column[1]
    for column in columns
}


# =========================================================
# ADD STATUS
# =========================================================

if "status" not in existing_columns:

    print("\nAdding status column...")

    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN status VARCHAR(20)
        DEFAULT 'published'
    """)

    print("status column added successfully!")

else:

    print("\nstatus column already exists.")


# =========================================================
# ADD SCHEDULED_AT
# =========================================================

if "scheduled_at" not in existing_columns:

    print("\nAdding scheduled_at column...")

    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN scheduled_at DATETIME
    """)

    print("scheduled_at column added successfully!")

else:

    print("\nscheduled_at column already exists.")


# =========================================================
# ADD PUBLISHED_AT
# =========================================================

if "published_at" not in existing_columns:

    print("\nAdding published_at column...")

    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN published_at DATETIME
    """)

    print("published_at column added successfully!")

else:

    print("\npublished_at column already exists.")


# =========================================================
# EXISTING POSTS
# =========================================================

# Existing posts were already published.
# Therefore, keep them as published.

cursor.execute("""
    UPDATE posts
    SET status = 'published'
    WHERE status IS NULL
       OR status = ''
""")


# =========================================================
# COMMIT
# =========================================================

conn.commit()


# =========================================================
# VERIFY
# =========================================================

columns = cursor.execute(
    "PRAGMA table_info(posts)"
).fetchall()

print("\nUpdated posts table structure:")

for column in columns:
    print(column)


conn.close()

print("\nPosts migration completed successfully!")