from celery_app import celery
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
    print(f"Starting scan task for domain: {domain}, session_id: {session_id}")
    print(f"Task ID: {self.request.id}")
    print(f"Results directory: {results_dir}")
    print(f"run_scan_task: Starting scan for domain {domain}, session_id {session_id}")
    print(f"run_scan_task: Task ID: {self.request.id if hasattr(self.request, 'id') else None}")
    print(f"run_scan_task: Results directory: {results_dir}")

    # Create a directory for this scan
    scan_dir = os.path.join(results_dir, session_id)
    print(f"run_scan_task: Scan directory: {scan_dir}")
    os.makedirs(scan_dir, exist_ok=True)
    print(f"run_scan_task: Created scan directory")

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
        try:
            # Only update state if running asynchronously (has task_id)
            if self.request.id:
                self.update_state(state='PROGRESS', meta={'progress': 0, 'current_tool': 'Subdomain Enumeration'})
        except Exception as e:
            print(f"Warning: Could not update task state: {str(e)}")

        # Always update the status file
        update_status(status_file, progress=0, current_tool='Subdomain Enumeration')

        subdomains_file = os.path.join(scan_dir, 'subdomains.txt')
        print(f"run_scan_task: Subdomains file: {subdomains_file}")
        print(f"run_scan_task: Starting subdomain enumeration for {domain}...")

        # Call run_subdomain_enumeration with the correct parameters
        # The function expects (domain, scan_dir, session_id, update_callback=None)
        subdomains = run_subdomain_enumeration(domain, scan_dir, session_id)
        print(f"run_scan_task: Subdomain enumeration completed")

        # No need to parse subdomains, as run_subdomain_enumeration already returns them
        if not subdomains:
            # If no subdomains were found, parse the file as a fallback
            subdomains = parse_subdomains(subdomains_file)
        update_status(status_file, progress=40, subdomains=subdomains)

        # Step 2: Web detection (30%)
        try:
            # Only update state if running asynchronously (has task_id)
            if self.request.id:
                self.update_state(state='PROGRESS', meta={'progress': 40, 'current_tool': 'Web Detection'})
        except Exception as e:
            print(f"Warning: Could not update task state: {str(e)}")

        # Always update the status file
        update_status(status_file, progress=40, current_tool='Web Detection')

        httpx_file = os.path.join(scan_dir, 'httpx.txt')
        print(f"run_scan_task: Starting web detection...")

        # Call run_web_detection with the correct parameters
        # The function expects (domain, subdomains, scan_dir, session_id, update_callback=None)
        live_hosts, urls = run_web_detection(domain, subdomains, scan_dir, session_id)
        print(f"run_scan_task: Web detection completed")

        # If no live hosts were found, parse the file as a fallback
        if not live_hosts:
            live_hosts = parse_httpx_output(httpx_file)
        update_status(status_file, progress=70, live_hosts=live_hosts)

        # Step 3: URL discovery (30%)
        try:
            # Only update state if running asynchronously (has task_id)
            if self.request.id:
                self.update_state(state='PROGRESS', meta={'progress': 70, 'current_tool': 'URL Discovery'})
        except Exception as e:
            print(f"Warning: Could not update task state: {str(e)}")

        # Always update the status file
        update_status(status_file, progress=70, current_tool='URL Discovery')

        # We already have URLs from the web detection step
        # But if they're empty, run gau separately
        if not urls:
            gau_file = os.path.join(scan_dir, 'gau.txt')
            print(f"run_scan_task: Starting URL discovery...")
            run_gau(domain, gau_file)
            print(f"run_scan_task: URL discovery completed")

            # Parse URLs
            urls = parse_gau_output(gau_file)
        update_status(status_file, progress=100, urls=urls, status='completed')

        # Final update
        try:
            # Only update state if running asynchronously (has task_id)
            if self.request.id:
                self.update_state(state='SUCCESS', meta={'progress': 100, 'current_tool': 'Completed'})
        except Exception as e:
            print(f"Warning: Could not update task state: {str(e)}")

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
        try:
            # Only update state if running asynchronously (has task_id)
            if self.request.id:
                self.update_state(state='FAILURE', meta={'error': error_msg})
        except Exception as e:
            print(f"Warning: Could not update task state: {str(e)}")

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
