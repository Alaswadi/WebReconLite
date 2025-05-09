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

# Create GAU configuration file
echo "Creating GAU configuration file..."
cat > /root/.gau.toml << 'EOL'
threads = 50
verbose = false
retries = 15
subdomains = false
parameters = false
providers = ["wayback","commoncrawl","otx","urlscan"]
blacklist = ["ttf","woff","svg","png","jpg"]
json = false

[urlscan]
  apikey = ""

[filters]
  from = ""
  to = ""
  matchstatuscodes = []
  matchmimetypes = []
  filterstatuscodes = []
  filtermimetypes = ["image/png", "image/jpg", "image/svg+xml"]
EOL

echo "GAU configuration file created at /root/.gau.toml"
cat /root/.gau.toml

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

    # Check available flags
    echo "Checking httpx available flags:"
    httpx -h 2>&1 | grep -E -- "-tech-detect|--tech-detect" && echo "  -tech-detect flag is available" || echo "  -tech-detect flag is NOT available"

    # Test with a simple domain
    echo "Testing httpx with example.com:"
    httpx -u example.com -silent || echo "httpx test failed"
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

if command -v naabu > /dev/null 2>&1; then
    echo "Testing naabu..."
    echo "Checking naabu version:"
    naabu -version || echo "naabu version check failed"

    # Test naabu with a simple scan
    echo "Testing naabu with a simple scan:"
    naabu -host example.com -p 80 -silent || echo "naabu test scan failed"
fi

if command -v sublist3r > /dev/null 2>&1; then
    echo "Testing sublist3r..."
    echo "Checking Sublist3r installation:"

    # Check possible locations
    if [ -f "/opt/Sublist3r/sublist3r.py" ]; then
        echo "  Found at: /opt/Sublist3r/sublist3r.py"
    elif [ -f "/app/Sublist3r/sublist3r.py" ]; then
        echo "  Found at: /app/Sublist3r/sublist3r.py"
    elif [ -f "$(pwd)/Sublist3r/sublist3r.py" ]; then
        echo "  Found at: $(pwd)/Sublist3r/sublist3r.py"
    elif [ -f "$(pwd)/sublist3r.py" ]; then
        echo "  Found at: $(pwd)/sublist3r.py"
    else
        echo "  WARNING: sublist3r wrapper is in PATH but sublist3r.py not found in expected locations"
        echo "  The wrapper script will use fallback mode"
    fi

    # Test the wrapper
    echo "  Testing wrapper with dummy domain..."
    sublist3r -d example.com -o /tmp/sublist3r_test.txt
    if [ -f "/tmp/sublist3r_test.txt" ]; then
        echo "  Wrapper test successful, created output file"
        cat /tmp/sublist3r_test.txt
        rm /tmp/sublist3r_test.txt
    else
        echo "  Wrapper test failed, no output file created"
    fi
fi

# Run the check-tools script to verify all tools are installed
echo "Checking installed tools..."
/usr/local/bin/check-tools.sh

# Initialize the database if it doesn't exist
echo "Initializing database..."
cd /app

# Create the data directory if it doesn't exist
mkdir -p /app/app/data

# Check if the database file exists
if [ ! -f /app/app/data/webreconlite.db ]; then
    echo "Database file does not exist, initializing..."
    # Initialize the database using Python
    python -c "from app.database import init_db; init_db()"
    echo "Database initialized."
else
    echo "Database file already exists at /app/app/data/webreconlite.db"
    echo "Size: $(du -h /app/app/data/webreconlite.db | cut -f1)"
    echo "Skipping initialization."
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8001 --workers 4 --timeout 120 --log-level debug wsgi:app
