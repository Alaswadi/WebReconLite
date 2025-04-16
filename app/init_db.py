#!/usr/bin/env python3
"""
Initialize the database if it doesn't exist.
This script is meant to be run when the container starts.
"""

import os
import sys
from database import init_db, ensure_data_dir, DB_FILE

def main():
    """Initialize the database if it doesn't exist."""
    print("Checking if database needs to be initialized...")

    # Ensure the data directory exists
    ensure_data_dir()

    # Check if the database file exists
    if os.path.exists(DB_FILE):
        print(f"Database already exists at {DB_FILE}")
        print("Skipping initialization.")
        return

    # Initialize the database
    if init_db():
        print("Database initialized successfully.")
    else:
        print("Failed to initialize database.")
        sys.exit(1)

if __name__ == "__main__":
    main()
