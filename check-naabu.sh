#!/bin/bash

echo "Checking if Naabu is installed..."
if command -v naabu &> /dev/null; then
    echo "Naabu is installed at: $(which naabu)"
    echo "Naabu version: $(naabu -version)"
    echo "Running a test scan on example.com..."
    naabu -host example.com -p 80,443 -silent
    echo "Scan completed."
else
    echo "Naabu is NOT installed!"
fi

echo "Checking if nmap is installed as a fallback..."
if command -v nmap &> /dev/null; then
    echo "nmap is installed at: $(which nmap)"
    echo "nmap version: $(nmap --version | head -n 1)"
else
    echo "nmap is NOT installed!"
fi
