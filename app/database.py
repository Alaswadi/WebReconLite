import os
import sqlite3
from sqlite3 import Error
import time

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'webreconlite.db')

def ensure_data_dir():
    """Ensure the data directory exists"""
    data_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def get_db_connection():
    """Create a database connection to the SQLite database"""
    ensure_data_dir()
    conn = None
    try:
        print(f"Connecting to database at {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        print(f"Successfully connected to database")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return None

def init_db():
    """Initialize the database with the required tables"""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Create DOMAINS table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS DOMAINS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Domain VARCHAR(255) NOT NULL UNIQUE,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create SUBDOMAINS table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SUBDOMAINS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DomainID INTEGER NOT NULL,
            Subdomain VARCHAR(255) NOT NULL,
            GauScanned INTEGER DEFAULT 0,
            NaabuScanned INTEGER DEFAULT 0,
            NucleiScanned INTEGER DEFAULT 0,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (DomainID) REFERENCES DOMAINS(ID),
            UNIQUE(DomainID, Subdomain)
        )
        ''')

        # Create GAU_TABLE
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS GAU_TABLE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            SID INTEGER NOT NULL,
            link VARCHAR(2048) NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (SID) REFERENCES SUBDOMAINS(ID),
            UNIQUE(SID, link)
        )
        ''')

        # Create NAABU_TABLE
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS NAABU_TABLE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            SID INTEGER NOT NULL,
            port INTEGER NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (SID) REFERENCES SUBDOMAINS(ID),
            UNIQUE(SID, port)
        )
        ''')

        # Create NUCLEI_TABLE
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS NUCLEI_TABLE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            SID INTEGER NOT NULL,
            vulnerability VARCHAR(255) NOT NULL,
            severity VARCHAR(50),
            details TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (SID) REFERENCES SUBDOMAINS(ID)
        )
        ''')

        conn.commit()
        print("Database initialized successfully")
        return True
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Domain operations
def add_domain(domain):
    """Add a domain to the database if it doesn't exist"""
    print(f"Adding domain to database: {domain}")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for adding domain: {domain}")
        return None

    try:
        cursor = conn.cursor()
        print(f"Executing INSERT OR IGNORE for domain: {domain}")
        cursor.execute("INSERT OR IGNORE INTO DOMAINS (Domain) VALUES (?)", (domain,))
        conn.commit()
        print(f"Committed domain insert for: {domain}")

        # Get the domain ID (either newly inserted or existing)
        print(f"Querying for domain ID for: {domain}")
        cursor.execute("SELECT ID FROM DOMAINS WHERE Domain = ?", (domain,))
        domain_id = cursor.fetchone()
        result = domain_id[0] if domain_id else None
        print(f"Domain ID for {domain}: {result}")
        return result
    except Error as e:
        print(f"Error adding domain: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()

def get_domain_id(domain):
    """Get the ID of a domain"""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM DOMAINS WHERE Domain = ?", (domain,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"Error getting domain ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Subdomain operations
def add_subdomain(domain_id, subdomain):
    """Add a subdomain to the database if it doesn't exist"""
    print(f"Adding subdomain to database: {subdomain} (Domain ID: {domain_id})")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for adding subdomain: {subdomain}")
        return None

    try:
        cursor = conn.cursor()
        print(f"Executing INSERT OR IGNORE for subdomain: {subdomain}")
        cursor.execute(
            "INSERT OR IGNORE INTO SUBDOMAINS (DomainID, Subdomain) VALUES (?, ?)",
            (domain_id, subdomain)
        )
        conn.commit()
        print(f"Committed subdomain insert for: {subdomain}")

        # Get the subdomain ID (either newly inserted or existing)
        print(f"Querying for subdomain ID for: {subdomain}")
        cursor.execute(
            "SELECT ID FROM SUBDOMAINS WHERE DomainID = ? AND Subdomain = ?",
            (domain_id, subdomain)
        )
        subdomain_id = cursor.fetchone()
        result = subdomain_id[0] if subdomain_id else None
        print(f"Subdomain ID for {subdomain}: {result}")
        return result
    except Error as e:
        print(f"Error adding subdomain: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()

def get_subdomain_id(domain_id, subdomain):
    """Get the ID of a subdomain"""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ID FROM SUBDOMAINS WHERE DomainID = ? AND Subdomain = ?",
            (domain_id, subdomain)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"Error getting subdomain ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_subdomain_scan_status(subdomain_id, scan_type, status=1):
    """Update the scan status of a subdomain"""
    print(f"Updating scan status for subdomain ID {subdomain_id}: {scan_type} = {status}")
    if scan_type not in ['GauScanned', 'NaabuScanned', 'NucleiScanned']:
        print(f"Invalid scan type: {scan_type}")
        return False

    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for updating scan status")
        return False

    try:
        cursor = conn.cursor()
        print(f"Executing UPDATE for subdomain ID {subdomain_id}: {scan_type} = {status}")
        cursor.execute(
            f"UPDATE SUBDOMAINS SET {scan_type} = ? WHERE ID = ?",
            (status, subdomain_id)
        )
        conn.commit()
        print(f"Committed scan status update for subdomain ID {subdomain_id}")

        # Verify the update was successful
        cursor.execute(f"SELECT {scan_type} FROM SUBDOMAINS WHERE ID = ?", (subdomain_id,))
        result = cursor.fetchone()
        if result and result[0] == status:
            print(f"Verified scan status update for subdomain ID {subdomain_id}: {scan_type} = {result[0]}")
            return True
        else:
            print(f"Failed to verify scan status update for subdomain ID {subdomain_id}")
            return False
    except Error as e:
        print(f"Error updating subdomain scan status: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

# GAU operations
def add_gau_result(subdomain_id, link):
    """Add a GAU result to the database"""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO GAU_TABLE (SID, link) VALUES (?, ?)",
            (subdomain_id, link)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error adding GAU result: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_gau_results_batch(subdomain_id, links):
    """Add multiple GAU results to the database in a batch"""
    if not links:
        return True

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        # Prepare data for batch insert
        data = [(subdomain_id, link) for link in links]
        cursor.executemany(
            "INSERT OR IGNORE INTO GAU_TABLE (SID, link) VALUES (?, ?)",
            data
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error adding GAU results batch: {e}")
        return False
    finally:
        if conn:
            conn.close()

# NAABU operations
def add_naabu_result(subdomain_id, port):
    """Add a NAABU result to the database"""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO NAABU_TABLE (SID, port) VALUES (?, ?)",
            (subdomain_id, port)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error adding NAABU result: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_naabu_results_batch(subdomain_id, ports):
    """Add multiple NAABU results to the database in a batch"""
    if not ports:
        return True

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        # Prepare data for batch insert
        data = [(subdomain_id, port) for port in ports]
        cursor.executemany(
            "INSERT OR IGNORE INTO NAABU_TABLE (SID, port) VALUES (?, ?)",
            data
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error adding NAABU results batch: {e}")
        return False
    finally:
        if conn:
            conn.close()

# NUCLEI operations
def add_nuclei_result(subdomain_id, vulnerability, severity=None, details=None):
    """Add a NUCLEI result to the database"""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO NUCLEI_TABLE (SID, vulnerability, severity, details) VALUES (?, ?, ?, ?)",
            (subdomain_id, vulnerability, severity, details)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error adding NUCLEI result: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Query operations for the scan history page
def get_domains_with_scans():
    """Get all domains that have subdomains"""
    print("Getting domains from database...")
    conn = get_db_connection()
    if conn is None:
        print("Failed to get database connection for getting domains")
        return []

    try:
        cursor = conn.cursor()

        # First, check if there are any domains in the database
        cursor.execute("SELECT COUNT(*) FROM DOMAINS")
        domain_count = cursor.fetchone()[0]
        print(f"Total domains in database: {domain_count}")

        # Then check if there are any subdomains
        cursor.execute("SELECT COUNT(*) FROM SUBDOMAINS")
        subdomain_count = cursor.fetchone()[0]
        print(f"Total subdomains in database: {subdomain_count}")

        # Also check how many are scanned (for debugging)
        cursor.execute("""
            SELECT COUNT(*) FROM SUBDOMAINS
            WHERE GauScanned = 1 OR NaabuScanned = 1 OR NucleiScanned = 1
        """)
        scanned_count = cursor.fetchone()[0]
        print(f"Total scanned subdomains: {scanned_count}")

        # Now get all domains that have subdomains
        print("Executing query to get all domains with subdomains...")
        cursor.execute("""
            SELECT DISTINCT d.ID, d.Domain
            FROM DOMAINS d
            JOIN SUBDOMAINS s ON d.ID = s.DomainID
            ORDER BY d.Domain
        """)
        results = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(results)} domains with scans")

        # Print the domains found
        for domain in results:
            print(f"  - Domain: {domain['Domain']} (ID: {domain['ID']})")

        return results
    except Error as e:
        print(f"Error getting domains with scans: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def get_scanned_subdomains(domain_id):
    """Get all subdomains for a domain"""
    print(f"Getting all subdomains for domain ID: {domain_id}")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for getting subdomains")
        return []

    try:
        cursor = conn.cursor()

        # First, check if the domain exists
        cursor.execute("SELECT Domain FROM DOMAINS WHERE ID = ?", (domain_id,))
        domain_result = cursor.fetchone()
        if domain_result:
            print(f"Found domain: {domain_result['Domain']}")
        else:
            print(f"Domain with ID {domain_id} not found")
            return []

        # Then check if there are any subdomains for this domain
        cursor.execute("SELECT COUNT(*) FROM SUBDOMAINS WHERE DomainID = ?", (domain_id,))
        subdomain_count = cursor.fetchone()[0]
        print(f"Total subdomains for domain ID {domain_id}: {subdomain_count}")

        # Also check how many are scanned (for debugging)
        cursor.execute("""
            SELECT COUNT(*) FROM SUBDOMAINS
            WHERE DomainID = ? AND (GauScanned = 1 OR NaabuScanned = 1 OR NucleiScanned = 1)
        """, (domain_id,))
        scanned_count = cursor.fetchone()[0]
        print(f"Total scanned subdomains for domain ID {domain_id}: {scanned_count}")

        # Now get all subdomains for this domain
        print(f"Executing query to get all subdomains for domain ID {domain_id}...")
        cursor.execute("""
            SELECT ID, Subdomain, GauScanned, NaabuScanned, NucleiScanned
            FROM SUBDOMAINS
            WHERE DomainID = ?
            ORDER BY Subdomain
        """, (domain_id,))
        results = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(results)} subdomains for domain ID {domain_id}")

        # Print the subdomains found
        for subdomain in results:
            print(f"  - Subdomain: {subdomain['Subdomain']} (ID: {subdomain['ID']})")
            print(f"    GAU: {'Scanned' if subdomain['GauScanned'] else 'Not Scanned'}")
            print(f"    Naabu: {'Scanned' if subdomain['NaabuScanned'] else 'Not Scanned'}")
            print(f"    Nuclei: {'Scanned' if subdomain['NucleiScanned'] else 'Not Scanned'}")

        return results
    except Error as e:
        print(f"Error getting scanned subdomains: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def get_gau_results(subdomain_id):
    """Get all GAU results for a subdomain"""
    print(f"Getting GAU results for subdomain ID: {subdomain_id}")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for GAU results")
        return []

    try:
        cursor = conn.cursor()

        # First check if there are any GAU results for this subdomain
        cursor.execute("SELECT COUNT(*) FROM GAU_TABLE WHERE SID = ?", (subdomain_id,))
        count = cursor.fetchone()[0]
        print(f"Found {count} GAU results for subdomain ID: {subdomain_id}")

        # Get the GAU results
        cursor.execute("""
            SELECT link
            FROM GAU_TABLE
            WHERE SID = ?
            ORDER BY link
        """, (subdomain_id,))
        results = [row['link'] for row in cursor.fetchall()]

        # Print a sample of the results
        if results:
            sample = results[:3] if len(results) > 3 else results
            print(f"Sample GAU results: {sample}")
            if len(results) > 3:
                print(f"... and {len(results) - 3} more")

        return results
    except Error as e:
        print(f"Error getting GAU results: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def get_naabu_results(subdomain_id):
    """Get all NAABU results for a subdomain"""
    print(f"Getting Naabu results for subdomain ID: {subdomain_id}")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for Naabu results")
        return []

    try:
        cursor = conn.cursor()

        # First check if there are any Naabu results for this subdomain
        cursor.execute("SELECT COUNT(*) FROM NAABU_TABLE WHERE SID = ?", (subdomain_id,))
        count = cursor.fetchone()[0]
        print(f"Found {count} Naabu results for subdomain ID: {subdomain_id}")

        # Get the Naabu results
        cursor.execute("""
            SELECT port
            FROM NAABU_TABLE
            WHERE SID = ?
            ORDER BY port
        """, (subdomain_id,))
        results = [row['port'] for row in cursor.fetchall()]

        # Print the results
        if results:
            print(f"Naabu results (ports): {results}")

        return results
    except Error as e:
        print(f"Error getting Naabu results: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def get_nuclei_results(subdomain_id):
    """Get all NUCLEI results for a subdomain"""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vulnerability, severity, details
            FROM NUCLEI_TABLE
            WHERE SID = ?
            ORDER BY severity DESC, vulnerability
        """, (subdomain_id,))
        return [dict(row) for row in cursor.fetchall()]
    except Error as e:
        print(f"Error getting NUCLEI results: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_subdomain_details(subdomain_id):
    """Get detailed information about a subdomain including scan results"""
    print(f"Getting details for subdomain ID: {subdomain_id}")
    conn = get_db_connection()
    if conn is None:
        print(f"Failed to get database connection for subdomain details")
        return None

    try:
        cursor = conn.cursor()
        # Get subdomain info
        print(f"Executing query to get subdomain info for ID: {subdomain_id}")
        cursor.execute("""
            SELECT s.ID, s.Subdomain, s.GauScanned, s.NaabuScanned, s.NucleiScanned, d.Domain
            FROM SUBDOMAINS s
            JOIN DOMAINS d ON s.DomainID = d.ID
            WHERE s.ID = ?
        """, (subdomain_id,))
        result = cursor.fetchone()
        if result:
            subdomain = dict(result)
            print(f"Found subdomain: {subdomain['Subdomain']} (Domain: {subdomain['Domain']})")
            print(f"Scan status: GAU={subdomain['GauScanned']}, Naabu={subdomain['NaabuScanned']}, Nuclei={subdomain['NucleiScanned']}")
        else:
            print(f"No subdomain found with ID: {subdomain_id}")
            return None

        # Get GAU results if scanned
        if subdomain.get('GauScanned'):
            print(f"Getting GAU results for subdomain ID: {subdomain_id}")
            subdomain['gau_results'] = get_gau_results(subdomain_id)
            print(f"Found {len(subdomain['gau_results'])} GAU results")

        # Get NAABU results if scanned
        if subdomain.get('NaabuScanned'):
            print(f"Getting Naabu results for subdomain ID: {subdomain_id}")
            subdomain['naabu_results'] = get_naabu_results(subdomain_id)
            print(f"Found {len(subdomain['naabu_results'])} Naabu results")

        # Get NUCLEI results if scanned
        if subdomain.get('NucleiScanned'):
            print(f"Getting Nuclei results for subdomain ID: {subdomain_id}")
            subdomain['nuclei_results'] = get_nuclei_results(subdomain_id)
            print(f"Found {len(subdomain['nuclei_results'])} Nuclei results")

        return subdomain
    except Error as e:
        print(f"Error getting subdomain details: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()
