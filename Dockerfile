# Use a multi-stage build approach
# Stage 1: Download pre-built binaries for tools
FROM alpine:latest AS tools-downloader

# Install dependencies
RUN apk add --no-cache curl unzip

# Create directory for tools
WORKDIR /tools

# Download subfinder
RUN echo "Downloading subfinder..." && \
    curl -L -o subfinder.zip https://github.com/projectdiscovery/subfinder/releases/download/v2.6.3/subfinder_2.6.3_linux_amd64.zip && \
    unzip subfinder.zip && \
    chmod +x subfinder && \
    rm subfinder.zip

# Download httpx
RUN echo "Downloading httpx..." && \
    curl -L -o httpx.zip https://github.com/projectdiscovery/httpx/releases/download/v1.3.7/httpx_1.3.7_linux_amd64.zip && \
    unzip httpx.zip && \
    chmod +x httpx && \
    rm httpx.zip

# Download chaos
RUN echo "Downloading chaos..." && \
    curl -L -o chaos.zip https://github.com/projectdiscovery/chaos-client/releases/download/v0.5.2/chaos-client_0.5.2_linux_amd64.zip && \
    unzip chaos.zip && \
    chmod +x chaos-client && \
    mv chaos-client chaos && \
    rm chaos.zip

# Stage 2: Build the Go tools (for tools that don't have pre-built binaries)
FROM golang:1.19 AS go-builder

# Set up Go environment
ENV GO111MODULE=on
ENV CGO_ENABLED=0

# Install dependencies
RUN apt-get update && apt-get install -y git

# Install assetfinder and gau
RUN echo "Installing assetfinder..." && \
    go install -v github.com/tomnomnom/assetfinder@latest || echo "Failed to install assetfinder"

RUN echo "Installing gau..." && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest || echo "Failed to install gau"

# List installed binaries
RUN ls -la /go/bin/

# Stage 3: Build the Python application
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

# Create directories for binaries
RUN mkdir -p /usr/local/bin

# Copy pre-built binaries from the tools-downloader stage
COPY --from=tools-downloader /tools/subfinder /usr/local/bin/
COPY --from=tools-downloader /tools/httpx /usr/local/bin/
COPY --from=tools-downloader /tools/chaos /usr/local/bin/

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

# Copy and set up the entrypoint script
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Run the healthcheck on startup
RUN /usr/local/bin/check-tools.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
