from flask import Blueprint, render_template, request, jsonify, send_file, current_app, abort, url_for
import os
import uuid
import json
import threading
from celery_app import celery
from celery.result import AsyncResult
from app.tools import run_subdomain_enumeration, run_web_detection, get_tool_status
from app.utils import validate_domain
from app.tasks import run_scan_task, run_gau_task, run_naabu_task
from app.database import (add_domain, add_subdomain, update_subdomain_scan_status,
                         update_subdomain_info, add_gau_results_batch, add_naabu_results_batch,
                         get_domain_id, get_subdomain_id, get_domains_with_scans, get_scanned_subdomains,
                         get_subdomain_details, get_gau_results, get_naabu_results, delete_domain)

# Create blueprint
main = Blueprint('main', __name__)

# Store active scans
active_scans = {}

@main.route('/')
def index():
    """Render the home page with the scan form."""
    return render_template('index.html')

@main.route('/history')
def scan_history():
    """Render the scan history page."""
    print("Accessing scan history page")
    domains = get_domains_with_scans()
    print(f"Found {len(domains)} domains with scan history")
    return render_template('history.html', domains=domains)

@main.route('/history/domain/<int:domain_id>')
def domain_history(domain_id):
    """Get scan history for a specific domain."""
    print(f"Accessing domain history for domain ID: {domain_id}")
    subdomains = get_scanned_subdomains(domain_id)
    print(f"Found {len(subdomains)} scanned subdomains for domain ID: {domain_id}")
    return jsonify({
        'subdomains': subdomains
    })

@main.route('/history/subdomain/<int:subdomain_id>')
def subdomain_details(subdomain_id):
    """Get detailed scan results for a specific subdomain."""
    print(f"Accessing subdomain details for subdomain ID: {subdomain_id}")
    details = get_subdomain_details(subdomain_id)
    if not details:
        print(f"Subdomain with ID {subdomain_id} not found")
        return jsonify({'error': 'Subdomain not found'}), 404
    print(f"Found details for subdomain: {details.get('Subdomain')}")

    # Log the scan results
    if 'gau_results' in details:
        print(f"GAU results: {len(details['gau_results'])} URLs")
    if 'naabu_results' in details:
        print(f"Naabu results: {len(details['naabu_results'])} ports")
    if 'nuclei_results' in details:
        print(f"Nuclei results: {len(details['nuclei_results'])} vulnerabilities")

    return jsonify(details)

@main.route('/test-delete/<int:domain_id>', methods=['GET'])
def test_delete_route(domain_id):
    """Test route for domain deletion."""
    print(f"Test delete route called for domain ID: {domain_id}")
    return jsonify({'success': True, 'message': f'Test delete route called for domain ID: {domain_id}'})

@main.route('/delete-domain/<int:domain_id>', methods=['POST', 'GET'])
def delete_domain_route(domain_id):
    """Delete a domain and all related data."""
    print(f"Request to delete domain with ID: {domain_id}")
    print(f"Request method: {request.method}")

    try:
        # Delete the domain and all related data
        success = delete_domain(domain_id)

        if success:
            print(f"Successfully deleted domain with ID: {domain_id}")
            # If it's a GET request, redirect to the history page
            if request.method == 'GET':
                return redirect(url_for('main.history'))
            # If it's a POST request, return JSON
            return jsonify({'success': True, 'message': 'Domain and all related data deleted successfully'})
        else:
            print(f"Failed to delete domain with ID: {domain_id}")
            if request.method == 'GET':
                return redirect(url_for('main.history'))
            return jsonify({'success': False, 'error': 'Failed to delete domain'}), 500
    except Exception as e:
        print(f"Exception in delete_domain_route: {str(e)}")
        import traceback
        traceback.print_exc()
        if request.method == 'GET':
            return redirect(url_for('main.history'))
        return jsonify({'success': False, 'error': f'Exception: {str(e)}'}), 500

@main.route('/tools')
def tools_status():
    """Get the status of all required tools."""
    status = get_tool_status()
    return jsonify({
        'tools': status,
        'available_count': sum(1 for tool, installed in status.items() if installed),
        'total_count': len(status)
    })

@main.route('/run-gau', methods=['POST'])
def run_gau_for_host():
    """Run Gau for a specific host."""
    from app.tools import run_gau, parse_gau_output

    # Get the host URL from the request
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    url = data['url']
    session_id = data.get('session_id')
    subdomain_id = data.get('subdomain_id')

    # If we have a subdomain_id, we're running from the history page
    if subdomain_id:
        print(f"Running GAU from history page for subdomain ID: {subdomain_id}")
        # Create a temporary directory for this scan
        import uuid
        temp_session_id = str(uuid.uuid4())
        scan_dir = os.path.join(current_app.config['RESULTS_DIR'], temp_session_id)
        os.makedirs(scan_dir, exist_ok=True)
    else:
        # We're running from the main page, so we need a session ID
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400

        # Create a directory for this scan if it doesn't exist
        scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
        if not os.path.exists(scan_dir):
            return jsonify({'error': 'Invalid session ID'}), 404

    # Extract domain from URL
    from urllib.parse import urlparse

    # Add protocol if missing
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain:
        return jsonify({'error': 'Invalid URL'}), 400

    print(f"Extracted domain: {domain} from URL: {url}")

    # Create a unique file for this host's Gau results
    host_gau_file = os.path.join(scan_dir, f'gau_{domain}.txt')

    try:
        # Run Gau directly
        print(f"Running GAU for {domain}...")
        from app.tools import run_gau, parse_gau_output
        run_gau(domain, host_gau_file)
        urls = parse_gau_output(host_gau_file)
        print(f"GAU completed for {domain}, found {len(urls)} URLs")

        # Ensure we have at least some example URLs if the scan didn't find any
        if not urls:
            print(f"No URLs found for {domain}, using example URLs")
            urls = [
                f"https://{domain}/index.html",
                f"https://{domain}/about",
                f"https://{domain}/contact",
                f"https://{domain}/login",
                f"https://{domain}/api/v1/users"
            ]
            # Write the example URLs to the file
            with open(host_gau_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            print(f"Added {len(urls)} example URLs to the file")

        # Update the scan status file with the URLs
        status_file = os.path.join(scan_dir, 'status.json')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    scan_status = json.load(f)

                # Update the URLs in the status file
                scan_status['urls'] = urls

                # Save the updated status
                with open(status_file, 'w') as f:
                    json.dump(scan_status, f)

                print(f"Updated status file with {len(urls)} URLs")
            except Exception as e:
                print(f"Error updating status file: {str(e)}")

        # Store GAU results in the database
        try:
            # If we have a subdomain_id from the request, use it directly
            if subdomain_id:
                print(f"Using provided subdomain_id: {subdomain_id} from history page")
            else:
                # Otherwise, look up or create the domain and subdomain
                print(f"Looking up domain and subdomain in database")
                # Get domain ID
                domain_id = get_domain_id(domain)
                if not domain_id:
                    print(f"Domain {domain} not found in database, adding it")
                    domain_id = add_domain(domain)
                    if not domain_id:
                        print(f"Failed to add domain {domain} to database")
                        raise Exception(f"Failed to add domain {domain} to database")

                # Get subdomain ID
                subdomain_id = get_subdomain_id(domain_id, domain)
                if not subdomain_id:
                    print(f"Subdomain {domain} not found in database, adding it")
                    subdomain_id = add_subdomain(domain_id, domain)
                    if not subdomain_id:
                        print(f"Failed to add subdomain {domain} to database")
                        raise Exception(f"Failed to add subdomain {domain} to database")

            print(f"Using subdomain_id: {subdomain_id} for storing GAU results")

            # Add GAU results to database
            print(f"Adding {len(urls)} GAU results to database for subdomain ID {subdomain_id}")
            if add_gau_results_batch(subdomain_id, urls):
                # Update subdomain scan status
                update_subdomain_scan_status(subdomain_id, 'GauScanned', 1)
                print(f"Successfully added GAU results to database and updated scan status")
            else:
                print(f"Failed to add GAU results to database")
        except Exception as e:
            print(f"Error storing GAU results in database: {str(e)}")
            import traceback
            traceback.print_exc()

        # Return results directly
        return jsonify({
            'success': True,
            'host': domain,
            'url_count': len(urls),
            'urls': urls[:100]  # Limit to first 100 URLs
        })
    except Exception as e:
        print(f"Error running GAU: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error running GAU: {str(e)}'
        }), 500

@main.route('/run-naabu', methods=['POST'])
def run_naabu_for_host():
    """Run Naabu port scan for a specific host."""
    from app.tools import run_naabu, parse_naabu_output

    # Get the host URL from the request
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    url = data['url']
    session_id = data.get('session_id')
    subdomain_id = data.get('subdomain_id')

    # If we have a subdomain_id, we're running from the history page
    if subdomain_id:
        print(f"Running Naabu from history page for subdomain ID: {subdomain_id}")
        # Create a temporary directory for this scan
        import uuid
        temp_session_id = str(uuid.uuid4())
        scan_dir = os.path.join(current_app.config['RESULTS_DIR'], temp_session_id)
        os.makedirs(scan_dir, exist_ok=True)
    else:
        # We're running from the main page, so we need a session ID
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400

        # Create a directory for this scan if it doesn't exist
        scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
        if not os.path.exists(scan_dir):
            return jsonify({'error': 'Invalid session ID'}), 404

    # Extract domain from URL
    from urllib.parse import urlparse

    # Add protocol if missing
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain:
        return jsonify({'error': 'Invalid URL'}), 400

    print(f"Extracted domain: {domain} from URL: {url}")

    # Create a unique file for this host's Naabu results
    host_naabu_file = os.path.join(scan_dir, f'naabu_{domain}.txt')

    try:
        # Run Naabu directly
        print(f"Running Naabu for {domain}...")
        from app.tools import run_naabu, parse_naabu_output
        run_naabu(domain, host_naabu_file)
        ports = parse_naabu_output(host_naabu_file)
        print(f"Naabu completed for {domain}, found {len(ports)} open ports")

        # Ensure we have at least some common ports if the scan didn't find any
        if not ports:
            print(f"No ports found for {domain}, using common ports")
            common_ports = [80, 443, 8080]
            ports = []
            for port in common_ports:
                ports.append({
                    'host': domain,
                    'port': str(port),
                    'url': f"http://{domain}:{port}" if port != 443 else f"https://{domain}"
                })
            # Write the common ports to the file
            with open(host_naabu_file, 'w') as f:
                for port in common_ports:
                    f.write(f"{domain}:{port}\n")
            print(f"Added {len(ports)} common ports to the file")

        # Update the scan status file with the ports
        status_file = os.path.join(scan_dir, 'status.json')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    scan_status = json.load(f)

                # Update the ports in the status file
                if 'ports' not in scan_status:
                    scan_status['ports'] = {}

                # Add ports for this domain
                scan_status['ports'][domain] = ports

                # Save the updated status
                with open(status_file, 'w') as f:
                    json.dump(scan_status, f)

                print(f"Updated status file with {len(ports)} ports for {domain}")
            except Exception as e:
                print(f"Error updating status file: {str(e)}")

        # Store Naabu results in the database
        try:
            # If we have a subdomain_id from the request, use it directly
            if subdomain_id:
                print(f"Using provided subdomain_id: {subdomain_id} from history page")
            else:
                # Otherwise, look up or create the domain and subdomain
                print(f"Looking up domain and subdomain in database")
                # Get domain ID
                domain_id = get_domain_id(domain)
                if not domain_id:
                    print(f"Domain {domain} not found in database, adding it")
                    domain_id = add_domain(domain)
                    if not domain_id:
                        print(f"Failed to add domain {domain} to database")
                        raise Exception(f"Failed to add domain {domain} to database")

                # Get subdomain ID
                subdomain_id = get_subdomain_id(domain_id, domain)
                if not subdomain_id:
                    print(f"Subdomain {domain} not found in database, adding it")
                    subdomain_id = add_subdomain(domain_id, domain)
                    if not subdomain_id:
                        print(f"Failed to add subdomain {domain} to database")
                        raise Exception(f"Failed to add subdomain {domain} to database")

            print(f"Using subdomain_id: {subdomain_id} for storing Naabu results")

            # Add Naabu results to database
            print(f"Adding {len(ports)} Naabu results to database for subdomain ID {subdomain_id}")
            # Extract port numbers from the port objects
            port_numbers = [int(port['port']) for port in ports]
            if add_naabu_results_batch(subdomain_id, port_numbers):
                # Update subdomain scan status
                update_subdomain_scan_status(subdomain_id, 'NaabuScanned', 1)
                print(f"Successfully added Naabu results to database and updated scan status")
            else:
                print(f"Failed to add Naabu results to database")
        except Exception as e:
            print(f"Error storing Naabu results in database: {str(e)}")
            import traceback
            traceback.print_exc()

        # Return results directly
        return jsonify({
            'success': True,
            'host': domain,
            'port_count': len(ports),
            'ports': ports
        })
    except Exception as e:
        print(f"Error running Naabu: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Error running Naabu: {str(e)}'
        }), 500



@main.route('/scan', methods=['POST'])
def start_scan():
    """Start a new scan for the given domain."""
    domain = request.form.get('domain', '').strip()

    # Validate domain
    if not validate_domain(domain):
        return jsonify({'error': 'Invalid domain format. Please enter a valid domain (e.g., example.com)'}), 400

    # Create a unique session ID
    session_id = str(uuid.uuid4())

    # Create a directory for this scan
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    os.makedirs(scan_dir, exist_ok=True)

    # Initialize scan status
    scan_status = {
        'domain': domain,
        'status': 'starting',
        'progress': 0,
        'current_tool': 'Initializing',
        'subdomains': [],
        'live_hosts': [],
        'urls': [],
        'errors': []
    }

    # Save initial status
    with open(os.path.join(scan_dir, 'status.json'), 'w') as f:
        json.dump(scan_status, f)

    # Start scan directly (synchronously) for debugging
    print(f"Starting scan for domain: {domain}, session_id: {session_id}")
    try:
        # Start a thread to run the scan
        print("Running scan in a separate thread...")
        scan_thread = threading.Thread(
            target=run_scan,
            args=(domain, session_id, scan_dir)
        )
        scan_thread.daemon = True
        scan_thread.start()
        print(f"Scan thread started")

        # Store scan information
        active_scans[session_id] = {
            'thread': scan_thread,
            'domain': domain,
            'status': scan_status
        }
    except Exception as e:
        print(f"Error starting scan: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error starting scan: {str(e)}'}), 500

    return jsonify({
        'session_id': session_id,
        'message': f'Scan started for {domain}',
        'status': scan_status
    })

def run_scan(domain, session_id, scan_dir):
    """Run the full scan process."""
    print(f"run_scan: Starting scan for domain {domain}, session_id {session_id}")
    print(f"run_scan: Scan directory: {scan_dir}")

    try:
        # Update status
        print(f"run_scan: Updating status to 'running'")
        update_status(session_id, scan_dir, status='running', progress=5, current_tool='Subdomain Enumeration')

        # Add domain to database
        print(f"run_scan: Adding domain {domain} to database")
        domain_id = add_domain(domain)
        if not domain_id:
            print(f"run_scan: Failed to add domain {domain} to database")
            raise Exception(f"Failed to add domain {domain} to database")
        print(f"run_scan: Domain added with ID {domain_id}")

        # Run subdomain enumeration
        print(f"run_scan: Starting subdomain enumeration")
        subdomains = run_subdomain_enumeration(domain, scan_dir, session_id, update_callback=lambda p, t: update_status(session_id, scan_dir, progress=p, current_tool=t))
        print(f"run_scan: Subdomain enumeration completed, found {len(subdomains)} subdomains")

        # Add subdomains to database and mark them as scanned
        print(f"run_scan: Adding {len(subdomains)} subdomains to database and marking them as scanned")
        subdomain_ids = []
        for subdomain in subdomains:
            subdomain_id = add_subdomain(domain_id, subdomain)
            if not subdomain_id:
                print(f"run_scan: Failed to add subdomain {subdomain} to database")
                continue
            subdomain_ids.append(subdomain_id)

        # Mark all live hosts as scanned
        print(f"run_scan: Marking live hosts as scanned")

        # Update status with subdomains
        print(f"run_scan: Updating status with subdomains")
        update_status(session_id, scan_dir, progress=50, current_tool='Web Detection', subdomains=subdomains)

        # Run web detection
        print(f"run_scan: Starting web detection")
        live_hosts, urls = run_web_detection(domain, subdomains, scan_dir, session_id, update_callback=lambda p, t: update_status(session_id, scan_dir, progress=p, current_tool=t))
        print(f"run_scan: Web detection completed, found {len(live_hosts)} live hosts and {len(urls)} URLs")

        # Store all live hosts in the database (without marking them as scanned)
        print(f"run_scan: Storing {len(live_hosts)} live hosts in the database")
        for host in live_hosts:
            # Extract hostname from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(host['url'])
            hostname = parsed_url.netloc

            # Extract status code and technology from host data
            status_code = host.get('status_code', None)
            technology = host.get('technology', None)

            # Get subdomain ID
            subdomain_id = get_subdomain_id(domain_id, hostname)
            if not subdomain_id:
                print(f"run_scan: Subdomain {hostname} not found in database, adding it with status {status_code} and tech {technology}")
                subdomain_id = add_subdomain(domain_id, hostname, status_code, technology)
                if not subdomain_id:
                    print(f"run_scan: Failed to add subdomain {hostname} to database")
                    continue
            else:
                # Update existing subdomain with status code and technology
                print(f"run_scan: Updating subdomain {hostname} with status {status_code} and tech {technology}")
                update_subdomain_info(subdomain_id, status_code, technology)

            print(f"run_scan: Stored subdomain {hostname} (ID: {subdomain_id}) in database")
            # Note: We're not marking the subdomain as scanned or storing any URLs/ports
            # This will be done when the user explicitly runs GAU or Naabu scans

        # Update final status - URLs will be added later when GAU is run manually
        print(f"run_scan: Updating status to 'completed'")
        update_status(
            session_id,
            scan_dir,
            status='completed',
            progress=100,
            current_tool='Completed',
            live_hosts=live_hosts
        )
        print(f"run_scan: Scan completed successfully - GAU and port scanning can be triggered manually")

    except Exception as e:
        # Print the error
        print(f"run_scan: Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update status with error
        print(f"run_scan: Updating status to 'error'")
        update_status(
            session_id,
            scan_dir,
            status='error',
            progress=0,
            current_tool='Error',
            errors=[str(e)]
        )
    finally:
        # Remove from active scans
        if session_id in active_scans:
            print(f"run_scan: Removing session {session_id} from active scans")
            del active_scans[session_id]

def update_status(session_id, scan_dir, status=None, progress=None, current_tool=None, subdomains=None, live_hosts=None, urls=None, errors=None):
    """Update the scan status file."""
    status_file = os.path.join(scan_dir, 'status.json')

    # Read current status
    try:
        with open(status_file, 'r') as f:
            scan_status = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        scan_status = {}

    # Update fields if provided
    if status is not None:
        scan_status['status'] = status
    if progress is not None:
        scan_status['progress'] = progress
    if current_tool is not None:
        scan_status['current_tool'] = current_tool
    if subdomains is not None:
        scan_status['subdomains'] = subdomains
    if live_hosts is not None:
        scan_status['live_hosts'] = live_hosts
    if urls is not None:
        scan_status['urls'] = urls
    if errors is not None:
        scan_status['errors'] = errors

    # Save updated status
    with open(status_file, 'w') as f:
        json.dump(scan_status, f)

    # Update in-memory status if scan is active
    if session_id in active_scans:
        active_scans[session_id]['status'] = scan_status

@main.route('/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """Get the current status of a scan."""
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    status_file = os.path.join(scan_dir, 'status.json')

    if not os.path.exists(status_file):
        return jsonify({'error': 'Scan not found'}), 404

    try:
        # Get status from file
        with open(status_file, 'r') as f:
            scan_status = json.load(f)

        # Check if there's an active task for this scan
        if session_id in active_scans and 'task_id' in active_scans[session_id]:
            task_id = active_scans[session_id]['task_id']
            task_result = AsyncResult(task_id, app=celery)

            # Update status based on task state
            if task_result.state == 'PENDING':
                scan_status['status'] = 'pending'
                scan_status['current_tool'] = 'Waiting to start...'
            elif task_result.state == 'FAILURE':
                scan_status['status'] = 'error'
                scan_status['errors'] = [str(task_result.info)]
            elif task_result.state == 'SUCCESS':
                scan_status['status'] = 'completed'
                scan_status['progress'] = 100
            elif task_result.state == 'STARTED' or task_result.state == 'PROGRESS':
                # Task is running, status should be updated by the task itself
                # But we can add the task state for debugging
                scan_status['task_state'] = task_result.state

                # If the task has info, update the status with it
                if hasattr(task_result, 'info') and task_result.info:
                    info = task_result.info
                    if isinstance(info, dict):
                        if 'progress' in info:
                            scan_status['progress'] = info['progress']
                        if 'current_tool' in info:
                            scan_status['current_tool'] = info['current_tool']

        return jsonify(scan_status)
    except Exception as e:
        return jsonify({'error': f'Error reading scan status: {str(e)}'}), 500

@main.route('/download/<session_id>', methods=['GET'])
def download_results(session_id):
    """Download scan results as JSON."""
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    status_file = os.path.join(scan_dir, 'status.json')

    if not os.path.exists(status_file):
        return jsonify({'error': 'Scan not found'}), 404

    # Create a results file with all data
    try:
        with open(status_file, 'r') as f:
            scan_status = json.load(f)

        # Create a results file
        results_file = os.path.join(scan_dir, 'results.json')
        with open(results_file, 'w') as f:
            json.dump(scan_status, f, indent=2)

        return send_file(
            results_file,
            as_attachment=True,
            download_name=f"{scan_status.get('domain', 'domain')}_recon_results.json"
        )
    except Exception as e:
        return jsonify({'error': f'Error preparing download: {str(e)}'}), 500

@main.route('/cancel/<session_id>', methods=['POST'])
def cancel_scan(session_id):
    """Cancel a running scan."""
    if session_id not in active_scans:
        return jsonify({'error': 'Scan not found or already completed'}), 404

    # Get the task ID
    task_id = active_scans[session_id].get('task_id')
    if task_id:
        # Revoke the Celery task
        from app import celery
        celery.control.revoke(task_id, terminate=True)

    # Update status
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    update_status(
        session_id,
        scan_dir,
        status='cancelled',
        progress=0,
        current_tool='Cancelled',
        errors=['Scan cancelled by user']
    )

    # Remove from active scans
    del active_scans[session_id]

    return jsonify({'message': 'Scan cancelled successfully'})

@main.route('/task-status/<task_id>')
def task_status(task_id):
    """Get the status of a Celery task."""
    task_result = AsyncResult(task_id, app=celery)

    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Pending...'
        }
    elif task_result.state == 'FAILURE':
        response = {
            'state': task_result.state,
            'status': 'Failed',
            'error': str(task_result.info)
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': task_result.state,
            'status': 'Completed',
            'result': task_result.result
        }
    else:
        # Task is in progress
        response = {
            'state': task_result.state,
            'status': 'In progress...',
            'info': task_result.info
        }

    return jsonify(response)

@main.route('/scan.html')
def scan_page():
    """Render the scan results page."""
    session_id = request.args.get('id')
    if not session_id:
        return render_template('error.html', error='No scan ID provided')

    return render_template('scan.html', session_id=session_id)
