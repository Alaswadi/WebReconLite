#!/bin/bash

# Script to create GAU configuration file inside the Docker container

echo "Creating GAU configuration file inside the Docker container..."

# Get the container ID
CONTAINER_ID=$(docker ps --filter "name=webreconlite" --format "{{.ID}}")

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: WebReconLite container not found. Make sure it's running."
    exit 1
fi

echo "Found container ID: $CONTAINER_ID"

# Create a temporary file with the GAU configuration
cat > temp_gau.toml << 'EOL'
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

# Copy the file to the container
docker cp temp_gau.toml ${CONTAINER_ID}:/root/.gau.toml

# Remove the temporary file
rm temp_gau.toml

# Verify the file was created
docker exec $CONTAINER_ID bash -c "if [ -f /root/.gau.toml ]; then echo 'GAU configuration file created successfully'; cat /root/.gau.toml; else echo 'Failed to create GAU configuration file'; fi"

echo "Done."
