#!/bin/bash

# Script to set up the GAU configuration file inside the Docker container

echo "Setting up GAU configuration file..."

# Create the GAU configuration file inside the container
docker-compose exec webreconlite bash -c "cat > /root/.gau.toml << 'EOL'
threads = 50 
verbose = false
retries = 15
subdomains = false
parameters = false
providers = [\"wayback\",\"commoncrawl\",\"otx\",\"urlscan\"]
blacklist = [\"ttf\",\"woff\",\"svg\",\"png\",\"jpg\"]
json = false

[urlscan]
  apikey = \"\"

[filters]
  from = \"\"
  to = \"\"
  matchstatuscodes = []
  matchmimetypes = []
  filterstatuscodes = []
  filtermimetypes = [\"image/png\", \"image/jpg\", \"image/svg+xml\"]
EOL"

# Check if the file was created successfully
docker-compose exec webreconlite bash -c "if [ -f /root/.gau.toml ]; then echo 'GAU configuration file created successfully'; cat /root/.gau.toml; else echo 'Failed to create GAU configuration file'; fi"

echo "Done."
