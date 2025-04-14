#!/usr/bin/env python3
import os
import sys
import sqlite3

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import (
    DB_FILE, init_db, get_db_connection, get_domains_with_scans,
    get_scanned_subdomains, get_subdomain_details
)

def check_db_file():
    """Check if the database file exists and its size."""
    print(f"Database file path: {DB_FILE}")
    
    if os.path.exists(DB_FILE):
        size = os.path.getsize(DB_FILE)
        print(f"Database file exists, size: {size} bytes")
        return True
    else:
        print(f"Database file does not exist")
        return False

def check_db_tables():
    """Check the database tables and their contents."""
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Get count for each table
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table {table}: {count} rows")
            
            # Show sample data for each table
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                print(f"Sample data from {table}:")
                for row in rows:
                    print(f"  {dict(row)}")
        
        return True
    except sqlite3.Error as e:
        print(f"Error checking database tables: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def check_domains_with_scans():
    """Check domains with scans in the database."""
    domains = get_domains_with_scans()
    print(f"Found {len(domains)} domains with scans")
    
    for domain in domains:
        print(f"Domain: {domain['Domain']} (ID: {domain['ID']})")
        
        # Check subdomains for this domain
        subdomains = get_scanned_subdomains(domain['ID'])
        print(f"  Found {len(subdomains)} scanned subdomains")
        
        for subdomain in subdomains:
            print(f"  Subdomain: {subdomain['Subdomain']} (ID: {subdomain['ID']})")
            print(f"    GAU: {'Scanned' if subdomain['GauScanned'] else 'Not Scanned'}")
            print(f"    Naabu: {'Scanned' if subdomain['NaabuScanned'] else 'Not Scanned'}")
            print(f"    Nuclei: {'Scanned' if subdomain['NucleiScanned'] else 'Not Scanned'}")
            
            # Check details for this subdomain
            details = get_subdomain_details(subdomain['ID'])
            if details:
                if 'gau_results' in details:
                    print(f"    GAU results: {len(details['gau_results'])} URLs")
                if 'naabu_results' in details:
                    print(f"    Naabu results: {len(details['naabu_results'])} ports")
                if 'nuclei_results' in details:
                    print(f"    Nuclei results: {len(details['nuclei_results'])} vulnerabilities")
            else:
                print(f"    Failed to get details for subdomain ID {subdomain['ID']}")

def main():
    """Main function to check the database."""
    print("Checking WebReconLite database...")
    
    # Check if the database file exists
    if not check_db_file():
        print("Initializing database...")
        if init_db():
            print("Database initialized successfully")
        else:
            print("Failed to initialize database")
            return
    
    # Check database tables
    print("\nChecking database tables...")
    check_db_tables()
    
    # Check domains with scans
    print("\nChecking domains with scans...")
    check_domains_with_scans()
    
    print("\nDatabase check completed")

if __name__ == "__main__":
    main()
