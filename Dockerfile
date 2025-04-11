# Use a multi-stage build approach
# Stage 1: Build the Go tools
FROM golang:1.19 AS go-builder

# Set up Go environment
ENV GO111MODULE=on
ENV CGO_ENABLED=0

# Install dependencies
RUN apt-get update && apt-get install -y git

# Install Go tools one by one with proper error handling
RUN echo "Installing subfinder..." && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || echo "Failed to install subfinder"

RUN echo "Installing assetfinder..." && \
    go install -v github.com/tomnomnom/assetfinder@latest || echo "Failed to install assetfinder"

RUN echo "Installing chaos..." && \
    go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest || echo "Failed to install chaos"

RUN echo "Installing httpx..." && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest || echo "Failed to install httpx"

RUN echo "Installing gau..." && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest || echo "Failed to install gau"

# List installed binaries
RUN ls -la /go/bin/

# Stage 2: Build the Python application
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    python3-pip \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Create directories for Go binaries
RUN mkdir -p /usr/local/bin

# Copy Go binaries from the builder stage
RUN mkdir -p /tmp/go-bins
COPY --from=go-builder /go/bin/ /tmp/go-bins/
RUN if [ -n "$(ls -A /tmp/go-bins 2>/dev/null)" ]; then \
      cp -r /tmp/go-bins/* /usr/local/bin/; \
    fi
RUN echo "Checking available binaries:" && ls -la /usr/local/bin/

# Install Sublist3r
RUN git clone https://github.com/aboul3la/Sublist3r.git /opt/Sublist3r || echo "Failed to clone Sublist3r"
RUN if [ -d "/opt/Sublist3r" ]; then \
        cd /opt/Sublist3r && \
        pip install -r requirements.txt || echo "Failed to install Sublist3r requirements"; \
    fi

# Copy and set up the Sublist3r wrapper script
COPY sublist3r-wrapper.sh /usr/local/bin/sublist3r
RUN chmod +x /usr/local/bin/sublist3r

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

# Copy and set up the healthcheck script
COPY check-tools.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/check-tools.sh

# Run the healthcheck on startup
RUN /usr/local/bin/check-tools.sh

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "4", "--timeout", "120", "app:app"]
