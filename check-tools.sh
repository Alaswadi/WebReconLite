#!/bin/bash

echo "Checking tool availability:"

# Count variables
total_tools=6
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
check_tool chaos
check_tool httpx
check_tool gau
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
