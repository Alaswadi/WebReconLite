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
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
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
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO DOMAINS (Domain) VALUES (?)", (domain,))
        conn.commit()
        
        # Get the domain ID (either newly inserted or existing)
        cursor.execute("SELECT ID FROM DOMAINS WHERE Domain = ?", (domain,))
        domain_id = cursor.fetchone()
        return domain_id[0] if domain_id else None
    except Error as e:
        print(f"Error adding domain: {e}")
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
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO SUBDOMAINS (DomainID, Subdomain) VALUES (?, ?)",
            (domain_id, subdomain)
        )
        conn.commit()
        
        # Get the subdomain ID (either newly inserted or existing)
        cursor.execute(
            "SELECT ID FROM SUBDOMAINS WHERE DomainID = ? AND Subdomain = ?",
            (domain_id, subdomain)
        )
        subdomain_id = cursor.fetchone()
        return subdomain_id[0] if subdomain_id else None
    except Error as e:
        print(f"Error adding subdomain: {e}")
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
    if scan_type not in ['GauScanned', 'NaabuScanned', 'NucleiScanned']:
        print(f"Invalid scan type: {scan_type}")
        return False
    
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE SUBDOMAINS SET {scan_type} = ? WHERE ID = ?",
            (status, subdomain_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Error updating subdomain scan status: {e}")
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
    """Get all domains that have at least one scanned subdomain"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT d.ID, d.Domain
            FROM DOMAINS d
            JOIN SUBDOMAINS s ON d.ID = s.DomainID
            WHERE s.GauScanned = 1 OR s.NaabuScanned = 1 OR s.NucleiScanned = 1
            ORDER BY d.Domain
        """)
        return [dict(row) for row in cursor.fetchall()]
    except Error as e:
        print(f"Error getting domains with scans: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_scanned_subdomains(domain_id):
    """Get all scanned subdomains for a domain"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Subdomain, GauScanned, NaabuScanned, NucleiScanned
            FROM SUBDOMAINS
            WHERE DomainID = ? AND (GauScanned = 1 OR NaabuScanned = 1 OR NucleiScanned = 1)
            ORDER BY Subdomain
        """, (domain_id,))
        return [dict(row) for row in cursor.fetchall()]
    except Error as e:
        print(f"Error getting scanned subdomains: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_gau_results(subdomain_id):
    """Get all GAU results for a subdomain"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT link
            FROM GAU_TABLE
            WHERE SID = ?
            ORDER BY link
        """, (subdomain_id,))
        return [row['link'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error getting GAU results: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_naabu_results(subdomain_id):
    """Get all NAABU results for a subdomain"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT port
            FROM NAABU_TABLE
            WHERE SID = ?
            ORDER BY port
        """, (subdomain_id,))
        return [row['port'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error getting NAABU results: {e}")
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
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        # Get subdomain info
        cursor.execute("""
            SELECT s.ID, s.Subdomain, s.GauScanned, s.NaabuScanned, s.NucleiScanned, d.Domain
            FROM SUBDOMAINS s
            JOIN DOMAINS d ON s.DomainID = d.ID
            WHERE s.ID = ?
        """, (subdomain_id,))
        subdomain = dict(cursor.fetchone() or {})
        
        if not subdomain:
            return None
        
        # Get GAU results if scanned
        if subdomain.get('GauScanned'):
            subdomain['gau_results'] = get_gau_results(subdomain_id)
        
        # Get NAABU results if scanned
        if subdomain.get('NaabuScanned'):
            subdomain['naabu_results'] = get_naabu_results(subdomain_id)
        
        # Get NUCLEI results if scanned
        if subdomain.get('NucleiScanned'):
            subdomain['nuclei_results'] = get_nuclei_results(subdomain_id)
        
        return subdomain
    except Error as e:
        print(f"Error getting subdomain details: {e}")
        return None
    finally:
        if conn:
            conn.close()
