import re
import os
import json
import uuid

def validate_domain(domain):
    """
    Validate if the input is a valid domain name.
    
    Args:
        domain (str): The domain to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Simple domain validation regex
    # Matches domains like example.com, sub.example.co.uk
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def deduplicate_list(items):
    """
    Remove duplicates from a list while preserving order.
    
    Args:
        items (list): List of items to deduplicate
        
    Returns:
        list: Deduplicated list
    """
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]

def generate_session_id():
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session ID
    """
    return str(uuid.uuid4())

def save_json(data, file_path):
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save
        file_path (str): Path to save the file
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(file_path):
    """
    Load JSON data from a file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Loaded JSON data or empty dict if file doesn't exist
    """
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r') as f:
        return json.load(f)

def sanitize_filename(filename):
    """
    Sanitize a filename to be safe for filesystem operations.
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    return re.sub(r'[\\/*?:"<>|]', '_', filename)
