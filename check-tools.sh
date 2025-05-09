#!/bin/bash

echo "Checking tool availability:"

# Count variables
total_tools=8  # Updated to include naabu and nmap
installed_tools=0

# Function to check if a tool is installed
check_tool() {
  local tool=$1
  local path=$(which $tool 2>/dev/null)

  if [ -n "$path" ]; then
    echo "$tool: ✅ Installed (Path: $path)"
    installed_tools=$((installed_tools + 1))
    return 0
  else
    echo "$tool: ❌ Not installed"
    return 1
  fi
}

# Check each tool
check_tool subfinder
check_tool assetfinder

# Special check for chaos with API key
if [ -n "$PDCP_API_KEY" ]; then
  check_tool chaos
  if [ $? -eq 0 ]; then
    echo "Testing chaos with API key..."
    chaos -key "$PDCP_API_KEY" -d example.com -count 1 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      echo "  Chaos API key is working properly."
    else
      echo "  Chaos API key test failed. The key might be invalid."
    fi
  fi
else
  echo "chaos: ❌ Not configured (PDCP_API_KEY not set)"
fi

# Special check for httpx with version and flag info
if check_tool httpx; then
  echo "Checking httpx version and flags:"
  httpx -version 2>&1 || echo "  No version flag found"
  httpx -h 2>&1 | grep -E -- "-tech-detect|--tech-detect" && echo "  -tech-detect flag is available" || echo "  -tech-detect flag is NOT available"
fi

# Special check for gau with version info
if check_tool gau; then
  echo "Checking gau version and flags:"
  gau -h 2>&1 | grep -E -- "-o|--o|-output|--output" || echo "  No output flag found in help"
  gau -version 2>&1 || gau --version 2>&1 || echo "  No version flag found"
fi

# Special check for naabu
if check_tool naabu; then
  echo "Checking naabu version:"
  naabu -version 2>&1 || echo "  No version flag found"
  echo "Testing naabu with a quick scan:"
  naabu -host example.com -p 80,443 -silent || echo "  Naabu test failed"
fi

# Special check for nmap
if check_tool nmap; then
  echo "Checking nmap version:"
  nmap --version | head -n 1 || echo "  No version flag found"
fi

check_tool sublist3r

# Print summary
echo ""
echo "$installed_tools out of $total_tools tools are installed."

# Check if any tools are missing
if [ $installed_tools -lt $total_tools ]; then
  missing_tools=$((total_tools - installed_tools))
  echo "$missing_tools tools are not installed!"
  echo "The application will use fallback mechanisms for missing tools."
else
  echo "All tools are installed! The application will use all available tools."
fi
