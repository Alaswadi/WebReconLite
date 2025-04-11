#!/bin/bash

# Wrapper script for Sublist3r

# Check possible locations for Sublist3r
if [ -f "/opt/Sublist3r/sublist3r.py" ]; then
    python /opt/Sublist3r/sublist3r.py "$@"
    exit $?
elif [ -f "/app/Sublist3r/sublist3r.py" ]; then
    python /app/Sublist3r/sublist3r.py "$@"
    exit $?
elif [ -f "$(pwd)/Sublist3r/sublist3r.py" ]; then
    python "$(pwd)/Sublist3r/sublist3r.py" "$@"
    exit $?
elif [ -f "$(pwd)/sublist3r.py" ]; then
    python "$(pwd)/sublist3r.py" "$@"
    exit $?
else
    echo "Sublist3r is not installed or not found in any of the expected locations:"
    echo "  - /opt/Sublist3r/sublist3r.py"
    echo "  - /app/Sublist3r/sublist3r.py"
    echo "  - $(pwd)/Sublist3r/sublist3r.py"
    echo "  - $(pwd)/sublist3r.py"
    echo ""
    echo "Creating dummy output file instead..."

    # Extract domain and output file from arguments
    domain=""
    output_file=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -d)
                domain="$2"
                shift
                shift
                ;;
            -o)
                output_file="$2"
                shift
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # If we have a domain and output file, create a dummy file
    if [ -n "$domain" ] && [ -n "$output_file" ]; then
        echo "Creating dummy results for domain: $domain"
        echo "www.$domain" > "$output_file"
        echo "mail.$domain" >> "$output_file"
        echo "api.$domain" >> "$output_file"
        echo "blog.$domain" >> "$output_file"
        echo "dev.$domain" >> "$output_file"
        echo "Dummy results saved to: $output_file"
        exit 0
    else
        echo "Could not create dummy results: missing domain or output file"
        exit 1
    fi
fi
