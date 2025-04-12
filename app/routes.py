from flask import Blueprint, render_template, request, jsonify, send_file, current_app, abort, url_for
import os
import uuid
import json
import threading
from celery.result import AsyncResult
from app.tools import run_subdomain_enumeration, run_web_detection, get_tool_status
from app.utils import validate_domain
from app.tasks import run_scan_task, run_gau_task, run_naabu_task

# Create blueprint
main = Blueprint('main', __name__)

# Store active scans
active_scans = {}

@main.route('/')
def index():
    """Render the home page with the scan form."""
    return render_template('index.html')

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

    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400

    # Create a directory for this scan if it doesn't exist
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    if not os.path.exists(scan_dir):
        return jsonify({'error': 'Invalid session ID'}), 404

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain:
        return jsonify({'error': 'Invalid URL'}), 400

    # Create a unique file for this host's Gau results
    host_gau_file = os.path.join(scan_dir, f'gau_{domain}.txt')

    try:
        # Run Gau as a Celery task
        task = run_gau_task.delay(domain, host_gau_file)

        # Return task ID for polling
        return jsonify({
            'success': True,
            'host': domain,
            'task_id': task.id,
            'status': 'processing'
        })
    except Exception as e:
        return jsonify({
            'error': f'Error starting Gau task: {str(e)}'
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

    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400

    # Create a directory for this scan if it doesn't exist
    scan_dir = os.path.join(current_app.config['RESULTS_DIR'], session_id)
    if not os.path.exists(scan_dir):
        return jsonify({'error': 'Invalid session ID'}), 404

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if not domain:
        return jsonify({'error': 'Invalid URL'}), 400

    # Create a unique file for this host's Naabu results
    host_naabu_file = os.path.join(scan_dir, f'naabu_{domain}.txt')

    try:
        # Run Naabu as a Celery task
        task = run_naabu_task.delay(domain, host_naabu_file)

        # Return task ID for polling
        return jsonify({
            'success': True,
            'host': domain,
            'task_id': task.id,
            'status': 'processing'
        })
    except Exception as e:
        return jsonify({
            'error': f'Error starting Naabu task: {str(e)}'
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

    # Start scan as a Celery task
    task = run_scan_task.delay(domain, session_id, current_app.config['RESULTS_DIR'])

    # Store task information for potential cancellation
    active_scans[session_id] = {
        'task_id': task.id,
        'domain': domain,
        'status': scan_status
    }

    return jsonify({
        'session_id': session_id,
        'message': f'Scan started for {domain}',
        'status': scan_status
    })

def run_scan(domain, session_id, scan_dir):
    """Run the full scan process."""
    try:
        # Update status
        update_status(session_id, scan_dir, status='running', progress=5, current_tool='Subdomain Enumeration')

        # Run subdomain enumeration
        subdomains = run_subdomain_enumeration(domain, scan_dir, session_id, update_callback=lambda p, t: update_status(session_id, scan_dir, progress=p, current_tool=t))

        # Update status with subdomains
        update_status(session_id, scan_dir, progress=50, current_tool='Web Detection', subdomains=subdomains)

        # Run web detection
        live_hosts, urls = run_web_detection(domain, subdomains, scan_dir, session_id, update_callback=lambda p, t: update_status(session_id, scan_dir, progress=p, current_tool=t))

        # Update final status
        update_status(
            session_id,
            scan_dir,
            status='completed',
            progress=100,
            current_tool='Completed',
            live_hosts=live_hosts,
            urls=urls
        )

    except Exception as e:
        # Update status with error
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
        with open(status_file, 'r') as f:
            scan_status = json.load(f)
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
    task_result = AsyncResult(task_id)

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
