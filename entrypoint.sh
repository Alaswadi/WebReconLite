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

# Check tool availability
echo "Checking tool availability:"
/usr/local/bin/check-tools.sh

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8001 --workers 4 --timeout 120 --log-level debug wsgi:app
