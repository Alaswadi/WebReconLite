#!/bin/bash

echo "Checking tool availability:"
for tool in subfinder assetfinder chaos httpx gau sublist3r; do
  if command -v $tool > /dev/null 2>&1; then
    echo "$tool: Installed"
  else
    echo "$tool: Not installed"
  fi
done
