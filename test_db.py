#!/usr/bin/env python3
import os
import sys
from app.database import (
    init_db, add_domain, add_subdomain, update_subdomain_scan_status,
    add_gau_results_batch, add_naabu_results_batch, get_domains_with_scans,
    get_scanned_subdomains, get_subdomain_details
)

def test_database():
    """Test the database functionality."""
    print("Initializing database...")
    if not init_db():
        print("Failed to initialize database")
        return False
    
    print("\nAdding test domain...")
    domain_id = add_domain("example.com")
    if not domain_id:
        print("Failed to add domain")
        return False
    print(f"Domain added with ID: {domain_id}")
    
    print("\nAdding test subdomains...")
    subdomains = ["www.example.com", "api.example.com", "mail.example.com"]
    subdomain_ids = []
    for subdomain in subdomains:
        subdomain_id = add_subdomain(domain_id, subdomain)
        if not subdomain_id:
            print(f"Failed to add subdomain: {subdomain}")
            continue
        subdomain_ids.append(subdomain_id)
        print(f"Subdomain added: {subdomain} with ID: {subdomain_id}")
    
    if not subdomain_ids:
        print("No subdomains were added")
        return False
    
    print("\nAdding test GAU results...")
    gau_results = [
        "https://www.example.com/login",
        "https://www.example.com/admin",
        "https://www.example.com/api/v1/users",
        "https://www.example.com/about",
        "https://www.example.com/contact"
    ]
    if add_gau_results_batch(subdomain_ids[0], gau_results):
        print(f"Added {len(gau_results)} GAU results for {subdomains[0]}")
        update_subdomain_scan_status(subdomain_ids[0], 'GauScanned', 1)
        print(f"Updated GAU scan status for {subdomains[0]}")
    else:
        print(f"Failed to add GAU results for {subdomains[0]}")
    
    print("\nAdding test Naabu results...")
    naabu_results = [80, 443, 8080, 8443]
    if add_naabu_results_batch(subdomain_ids[1], naabu_results):
        print(f"Added {len(naabu_results)} Naabu results for {subdomains[1]}")
        update_subdomain_scan_status(subdomain_ids[1], 'NaabuScanned', 1)
        print(f"Updated Naabu scan status for {subdomains[1]}")
    else:
        print(f"Failed to add Naabu results for {subdomains[1]}")
    
    print("\nGetting domains with scans...")
    domains = get_domains_with_scans()
    print(f"Found {len(domains)} domains with scans:")
    for domain in domains:
        print(f"  - {domain['Domain']} (ID: {domain['ID']})")
    
    if domains:
        print("\nGetting scanned subdomains for domain ID:", domains[0]['ID'])
        scanned_subdomains = get_scanned_subdomains(domains[0]['ID'])
        print(f"Found {len(scanned_subdomains)} scanned subdomains:")
        for subdomain in scanned_subdomains:
            print(f"  - {subdomain['Subdomain']} (ID: {subdomain['ID']})")
            print(f"    GAU: {'Scanned' if subdomain['GauScanned'] else 'Not Scanned'}")
            print(f"    Naabu: {'Scanned' if subdomain['NaabuScanned'] else 'Not Scanned'}")
            print(f"    Nuclei: {'Scanned' if subdomain['NucleiScanned'] else 'Not Scanned'}")
            
            if subdomain['GauScanned'] or subdomain['NaabuScanned']:
                print("\nGetting subdomain details for ID:", subdomain['ID'])
                details = get_subdomain_details(subdomain['ID'])
                if details:
                    if 'gau_results' in details and details['gau_results']:
                        print(f"  GAU Results ({len(details['gau_results'])} URLs):")
                        for url in details['gau_results'][:5]:  # Show first 5 URLs
                            print(f"    - {url}")
                        if len(details['gau_results']) > 5:
                            print(f"    ... and {len(details['gau_results']) - 5} more")
                    
                    if 'naabu_results' in details and details['naabu_results']:
                        print(f"  Naabu Results ({len(details['naabu_results'])} ports):")
                        for port in details['naabu_results']:
                            print(f"    - {port}")
                else:
                    print("  No details found for this subdomain")
    
    print("\nDatabase test completed successfully!")
    return True

if __name__ == "__main__":
    # Add the parent directory to the path so we can import the app module
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Run the test
    test_database()
