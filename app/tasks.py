from app import celery
import os
import json
import time
from app.tools import (
    run_subdomain_enumeration,
    run_web_detection,
    run_gau,
    run_naabu,
    parse_subdomains,
    parse_httpx_output,
    parse_gau_output,
    parse_naabu_output
)

@celery.task(bind=True)
def run_scan_task(self, domain, session_id, results_dir):
    """
    Celery task to run a full scan asynchronously.
    
    Args:
        domain (str): The domain to scan
        session_id (str): The unique session ID for this scan
        results_dir (str): The directory to store results
    """
    # Create a directory for this scan
    scan_dir = os.path.join(results_dir, session_id)
    os.makedirs(scan_dir, exist_ok=True)
    
    # Create status file
    status_file = os.path.join(scan_dir, 'status.json')
    
    # Initialize status
    status = {
        'domain': domain,
        'status': 'running',
        'progress': 0,
        'current_tool': 'Initializing',
        'subdomains': [],
        'live_hosts': [],
        'urls': [],
        'errors': []
    }
    
    # Save initial status
    with open(status_file, 'w') as f:
        json.dump(status, f)
    
    try:
        # Step 1: Subdomain enumeration (40%)
        self.update_state(state='PROGRESS', meta={'progress': 0, 'current_tool': 'Subdomain Enumeration'})
        update_status(status_file, progress=0, current_tool='Subdomain Enumeration')
        
        subdomains_file = os.path.join(scan_dir, 'subdomains.txt')
        run_subdomain_enumeration(domain, subdomains_file)
        
        # Parse subdomains
        subdomains = parse_subdomains(subdomains_file)
        update_status(status_file, progress=40, subdomains=subdomains)
        
        # Step 2: Web detection (30%)
        self.update_state(state='PROGRESS', meta={'progress': 40, 'current_tool': 'Web Detection'})
        update_status(status_file, progress=40, current_tool='Web Detection')
        
        httpx_file = os.path.join(scan_dir, 'httpx.txt')
        run_web_detection(subdomains_file, httpx_file)
        
        # Parse live hosts
        live_hosts = parse_httpx_output(httpx_file)
        update_status(status_file, progress=70, live_hosts=live_hosts)
        
        # Step 3: URL discovery (30%)
        self.update_state(state='PROGRESS', meta={'progress': 70, 'current_tool': 'URL Discovery'})
        update_status(status_file, progress=70, current_tool='URL Discovery')
        
        gau_file = os.path.join(scan_dir, 'gau.txt')
        run_gau(domain, gau_file)
        
        # Parse URLs
        urls = parse_gau_output(gau_file)
        update_status(status_file, progress=100, urls=urls, status='completed')
        
        # Final update
        self.update_state(state='SUCCESS', meta={'progress': 100, 'current_tool': 'Completed'})
        
        return {
            'domain': domain,
            'session_id': session_id,
            'status': 'completed',
            'subdomains_count': len(subdomains),
            'live_hosts_count': len(live_hosts),
            'urls_count': len(urls)
        }
        
    except Exception as e:
        # Update status with error
        error_msg = f"Error during scan: {str(e)}"
        update_status(status_file, status='error', errors=[error_msg])
        
        # Update Celery task state
        self.update_state(state='FAILURE', meta={'error': error_msg})
        
        # Re-raise the exception
        raise

@celery.task(bind=True)
def run_gau_task(self, domain, output_file):
    """
    Celery task to run Gau for a specific domain.
    
    Args:
        domain (str): The domain to scan with Gau
        output_file (str): The file to save results to
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Running Gau...'})
        run_gau(domain, output_file)
        urls = parse_gau_output(output_file)
        
        return {
            'status': 'completed',
            'domain': domain,
            'url_count': len(urls),
            'urls': urls[:100]  # Limit to first 100 URLs
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery.task(bind=True)
def run_naabu_task(self, domain, output_file):
    """
    Celery task to run Naabu for a specific domain.
    
    Args:
        domain (str): The domain to scan with Naabu
        output_file (str): The file to save results to
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Running Naabu...'})
        run_naabu(domain, output_file)
        ports = parse_naabu_output(output_file)
        
        return {
            'status': 'completed',
            'domain': domain,
            'port_count': len(ports),
            'ports': ports
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

def update_status(status_file, **kwargs):
    """
    Update the status file with new information.
    
    Args:
        status_file (str): Path to the status file
        **kwargs: Key-value pairs to update in the status
    """
    try:
        # Read current status
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        # Update status with new values
        status.update(kwargs)
        
        # Write updated status
        with open(status_file, 'w') as f:
            json.dump(status, f)
            
    except Exception as e:
        print(f"Error updating status file: {str(e)}")
