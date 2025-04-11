#!/bin/bash
set -e

# Print Python version
echo "Python version:"
python --version

# Print installed packages
echo "Installed Python packages:"
pip list

# Check if the app directory exists
echo "Checking app directory:"
ls -la /app

# Check if the wsgi.py file exists
echo "Checking wsgi.py file:"
if [ -f /app/wsgi.py ]; then
    echo "wsgi.py exists"
else
    echo "wsgi.py does not exist"
    exit 1
fi

# Check if the app directory exists
echo "Checking app directory structure:"
if [ -d /app/app ]; then
    echo "app directory exists"
    ls -la /app/app
else
    echo "app directory does not exist"
    exit 1
fi

# Check for API keys
if [ -n "$PDCP_API_KEY" ]; then
    echo "PDCP_API_KEY is set. Chaos should work properly."
else
    echo "WARNING: PDCP_API_KEY is not set. Chaos will not work properly."
fi

# Check tool availability
echo "Checking tool availability:"
/usr/local/bin/check-tools.sh

# Test each tool
echo "\nTesting tools:\n"

if command -v subfinder > /dev/null 2>&1; then
    echo "Testing subfinder..."
    subfinder -version || echo "subfinder version check failed"
fi

if command -v httpx > /dev/null 2>&1; then
    echo "Testing httpx..."
    httpx -version || echo "httpx version check failed"
fi

if command -v chaos > /dev/null 2>&1; then
    echo "Testing chaos..."
    chaos -version || echo "chaos version check failed"
fi

if command -v assetfinder > /dev/null 2>&1; then
    echo "Testing assetfinder..."
    echo "assetfinder has no version flag, but it's in PATH"
fi

if command -v gau > /dev/null 2>&1; then
    echo "Testing gau..."
    echo "Checking gau version and available flags:"
    gau -h || gau --help || echo "gau help check failed"
    gau -version || gau --version || echo "gau version check failed"

    # Try to determine which output flag to use
    echo "Checking gau output flags:"
    gau -h 2>&1 | grep -E -- "-o|--o|-output|--output" || echo "No output flag found in help"
fi

if command -v sublist3r > /dev/null 2>&1; then
    echo "Testing sublist3r..."
    echo "sublist3r has no version flag, but it's in PATH"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8001 --workers 4 --timeout 120 --log-level debug wsgi:app
