#!/usr/bin/env python3
"""
Check the status of the database.
This script is meant to be run manually to check the database status.
"""

import os
import sys
from app.database import get_db_connection, DB_FILE

def main():
    """Check the status of the database."""
    print(f"Checking database status at {DB_FILE}...")

    # Check if the database file exists
    if not os.path.exists(DB_FILE):
        print(f"Database file does not exist at {DB_FILE}")
        return

    # Check the file size
    file_size = os.path.getsize(DB_FILE)
    print(f"Database file size: {file_size} bytes")

    # Try to connect to the database
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database.")
        return

    try:
        # Check the number of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Number of tables: {len(tables)}")
        print("Tables:")
        for table in tables:
            print(f"  - {table['name']}")

            # Get the number of rows in each table
            cursor.execute(f"SELECT COUNT(*) FROM {table['name']}")
            row_count = cursor.fetchone()[0]
            print(f"    Rows: {row_count}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
