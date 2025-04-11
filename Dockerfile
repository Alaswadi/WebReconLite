# Use a multi-stage build approach
# Stage 1: Build the Go tools
FROM golang:1.19 AS go-builder

# Install Go tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || echo "Failed to install subfinder"
RUN go install -v github.com/tomnomnom/assetfinder@latest || echo "Failed to install assetfinder"
RUN go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest || echo "Failed to install chaos"
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest || echo "Failed to install httpx"
RUN go install -v github.com/lc/gau/v2/cmd/gau@latest || echo "Failed to install gau"

# Stage 2: Build the Python application
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directories for Go binaries
RUN mkdir -p /usr/local/bin

# Copy Go binaries from the builder stage
COPY --from=go-builder /go/bin/* /usr/local/bin/ || echo "No Go binaries to copy"

# Install Sublist3r
RUN git clone https://github.com/aboul3la/Sublist3r.git /opt/Sublist3r || echo "Failed to clone Sublist3r"
RUN if [ -d "/opt/Sublist3r" ]; then \
        cd /opt/Sublist3r && \
        pip install -r requirements.txt || echo "Failed to install Sublist3r requirements"; \
    fi

# Create a wrapper script for Sublist3r
RUN if [ -d "/opt/Sublist3r" ]; then \
        echo '#!/bin/bash\npython /opt/Sublist3r/sublist3r.py "$@"' > /usr/local/bin/sublist3r && \
        chmod +x /usr/local/bin/sublist3r; \
    fi

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create results directory
RUN mkdir -p app/results

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Create a healthcheck script
RUN echo '#!/bin/bash\necho "Checking tool availability:"\nfor tool in subfinder assetfinder chaos httpx gau sublist3r; do\n  if command -v $tool > /dev/null; then\n    echo "$tool: Installed"\n  else\n    echo "$tool: Not installed"\n  fi\ndone' > /usr/local/bin/check-tools.sh && \
    chmod +x /usr/local/bin/check-tools.sh

# Run the healthcheck on startup
RUN /usr/local/bin/check-tools.sh

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "4", "--timeout", "120", "app:app"]
