#!/bin/bash

# Wrapper script for Sublist3r
if [ -f "/opt/Sublist3r/sublist3r.py" ]; then
    python /opt/Sublist3r/sublist3r.py "$@"
else
    echo "Sublist3r is not installed or not found at /opt/Sublist3r/sublist3r.py"
    echo "This is a wrapper script that would normally run Sublist3r."
    exit 1
fi
