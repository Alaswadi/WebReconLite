import subprocess
import os
import time
import threading
import json
from app.utils import deduplicate_list

def run_tool(tool_name, command, output_file=None, timeout=300):
    """Run a command-line tool and capture its output."""
    try:
        # Start the process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE if output_file else None,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # Wait for the process to complete with timeout
        stdout, stderr = process.communicate(timeout=timeout)
        
        # Check if the process was successful
        if process.returncode != 0:
            raise Exception(f"{tool_name} failed: {stderr}")
        
        # Save output to file if specified
        if output_file and stdout:
            with open(output_file, 'w') as f:
                f.write(stdout)
            
        return stdout if stdout else ""
    
    except subprocess.TimeoutExpired:
        # Kill the process if it times out
        process.kill()
        raise Exception(f"{tool_name} timed out after {timeout} seconds")
    
    except Exception as e:
        # Handle other exceptions
        raise Exception(f"Error running {tool_name}: {str(e)}")

def run_subfinder(domain, output_file):
    """Run Subfinder for subdomain enumeration."""
    command = f"subfinder -d {domain} -silent"
    return run_tool("Subfinder", command, output_file)

def run_assetfinder(domain, output_file):
    """Run Assetfinder for subdomain enumeration."""
    command = f"assetfinder {domain}"
    return run_tool("Assetfinder", command, output_file)

def run_chaos(domain, output_file):
    """Run Chaos for subdomain enumeration."""
    command = f"chaos -d {domain} -silent"
    return run_tool("Chaos", command, output_file)

def run_sublist3r(domain, output_file):
    """Run Sublist3r for subdomain enumeration."""
    command = f"python3 sublist3r.py -d {domain} -o {output_file}"
    return run_tool("Sublist3r", command)

def run_httpx(subdomains_file, output_file):
    """Run Httpx for web detection."""
    command = f"httpx -l {subdomains_file} -silent -title -status-code -o {output_file}"
    return run_tool("Httpx", command)

def run_gau(domain, output_file):
    """Run Gau for URL discovery."""
    command = f"gau {domain} -o {output_file}"
    return run_tool("Gau", command)

def parse_subdomains(file_path):
    """Parse subdomains from a file."""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def parse_httpx_output(file_path):
    """Parse Httpx output to extract live hosts."""
    if not os.path.exists(file_path):
        return []
    
    live_hosts = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Parse line format: https://example.com [200] [Page Title]
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue
            
            url = parts[0]
            
            # Extract status code
            status_code = "Unknown"
            if '[' in parts[1] and ']' in parts[1]:
                status_start = parts[1].find('[') + 1
                status_end = parts[1].find(']', status_start)
                if status_start < status_end:
                    status_code = parts[1][status_start:status_end]
            
            # Extract title
            title = "No Title"
            title_start = parts[1].find('[', parts[1].find(']') + 1) + 1
            if title_start > 0:
                title_end = parts[1].find(']', title_start)
                if title_end > title_start:
                    title = parts[1][title_start:title_end]
            
            live_hosts.append({
                'url': url,
                'status_code': status_code,
                'title': title
            })
    
    return live_hosts

def parse_gau_output(file_path):
    """Parse Gau output to extract URLs."""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def run_subdomain_enumeration(domain, scan_dir, session_id, update_callback=None):
    """Run all subdomain enumeration tools concurrently."""
    # Create output files
    subfinder_file = os.path.join(scan_dir, 'subfinder.txt')
    assetfinder_file = os.path.join(scan_dir, 'assetfinder.txt')
    chaos_file = os.path.join(scan_dir, 'chaos.txt')
    sublist3r_file = os.path.join(scan_dir, 'sublist3r.txt')
    
    # Store results
    results = {
        'subfinder': [],
        'assetfinder': [],
        'chaos': [],
        'sublist3r': []
    }
    
    # Store errors
    errors = []
    
    # Function to run a tool and update progress
    def run_tool_with_progress(tool_func, tool_name, domain, output_file, results_key):
        try:
            if update_callback:
                update_callback(5, f"Running {tool_name}")
            
            tool_func(domain, output_file)
            results[results_key] = parse_subdomains(output_file)
            
            if update_callback:
                update_callback(10, f"Completed {tool_name}")
        
        except Exception as e:
            errors.append(f"{tool_name} error: {str(e)}")
            if update_callback:
                update_callback(10, f"{tool_name} failed: {str(e)}")
    
    # Create threads for each tool
    threads = [
        threading.Thread(target=run_tool_with_progress, args=(run_subfinder, "Subfinder", domain, subfinder_file, 'subfinder')),
        threading.Thread(target=run_tool_with_progress, args=(run_assetfinder, "Assetfinder", domain, assetfinder_file, 'assetfinder')),
        threading.Thread(target=run_tool_with_progress, args=(run_tool_with_progress, "Chaos", domain, chaos_file, 'chaos')),
        threading.Thread(target=run_tool_with_progress, args=(run_sublist3r, "Sublist3r", domain, sublist3r_file, 'sublist3r'))
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Combine and deduplicate results
    all_subdomains = []
    for key, subdomains in results.items():
        all_subdomains.extend(subdomains)
    
    unique_subdomains = deduplicate_list(all_subdomains)
    
    # Save combined results
    combined_file = os.path.join(scan_dir, 'subdomains.txt')
    with open(combined_file, 'w') as f:
        for subdomain in unique_subdomains:
            f.write(f"{subdomain}\n")
    
    return unique_subdomains

def run_web_detection(domain, subdomains, scan_dir, session_id, update_callback=None):
    """Run web detection tools."""
    # Create output files
    subdomains_file = os.path.join(scan_dir, 'subdomains.txt')
    httpx_file = os.path.join(scan_dir, 'httpx.txt')
    gau_file = os.path.join(scan_dir, 'gau.txt')
    
    # Ensure subdomains file exists
    if not os.path.exists(subdomains_file):
        with open(subdomains_file, 'w') as f:
            for subdomain in subdomains:
                f.write(f"{subdomain}\n")
    
    # Run Httpx
    try:
        if update_callback:
            update_callback(60, "Running Httpx")
        
        run_httpx(subdomains_file, httpx_file)
        live_hosts = parse_httpx_output(httpx_file)
        
        if update_callback:
            update_callback(80, "Completed Httpx")
    
    except Exception as e:
        if update_callback:
            update_callback(80, f"Httpx failed: {str(e)}")
        live_hosts = []
    
    # Run Gau
    try:
        if update_callback:
            update_callback(85, "Running Gau")
        
        run_gau(domain, gau_file)
        urls = parse_gau_output(gau_file)
        
        if update_callback:
            update_callback(95, "Completed Gau")
    
    except Exception as e:
        if update_callback:
            update_callback(95, f"Gau failed: {str(e)}")
        urls = []
    
    return live_hosts, urls
