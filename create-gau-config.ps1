# PowerShell script to create GAU configuration file inside the Docker container

Write-Host "Creating GAU configuration file inside the Docker container..."

# Get the container ID
$containerId = docker ps --filter "name=webreconlite" --format "{{.ID}}"

if (-not $containerId) {
    Write-Host "Error: WebReconLite container not found. Make sure it's running."
    exit 1
}

Write-Host "Found container ID: $containerId"

# Create the GAU configuration file
$gauConfig = @"
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
"@

# Write the configuration to a temporary file
$gauConfig | Out-File -FilePath "temp_gau.toml" -Encoding utf8

# Copy the file to the container
docker cp temp_gau.toml ${containerId}:/root/.gau.toml

# Remove the temporary file
Remove-Item -Path "temp_gau.toml"

# Verify the file was created
docker exec $containerId bash -c "if [ -f /root/.gau.toml ]; then echo 'GAU configuration file created successfully'; cat /root/.gau.toml; else echo 'Failed to create GAU configuration file'; fi"

Write-Host "Done."
