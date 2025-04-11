# Use a multi-stage build approach
# Stage 1: Build the Go tools
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
    golang \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Set up Go environment
ENV GOPATH /root/go
ENV PATH $PATH:/root/go/bin

# Install subfinder
RUN echo "Installing subfinder..." && \
    curl -L -o subfinder.zip https://github.com/projectdiscovery/subfinder/releases/download/v2.6.3/subfinder_2.6.3_linux_amd64.zip && \
    unzip -o subfinder.zip -d /tmp && \
    mv /tmp/subfinder /usr/local/bin/ && \
    chmod +x /usr/local/bin/subfinder && \
    rm subfinder.zip

# Install httpx
RUN echo "Installing httpx..." && \
    curl -L -o httpx.zip https://github.com/projectdiscovery/httpx/releases/download/v1.3.7/httpx_1.3.7_linux_amd64.zip && \
    unzip -o httpx.zip -d /tmp && \
    mv /tmp/httpx /usr/local/bin/ && \
    chmod +x /usr/local/bin/httpx && \
    rm httpx.zip

# Install chaos
RUN echo "Installing chaos..." && \
    curl -L -o chaos.zip https://github.com/projectdiscovery/chaos-client/releases/download/v0.5.2/chaos-client_0.5.2_linux_amd64.zip && \
    unzip -o chaos.zip -d /tmp && \
    mv /tmp/chaos-client /usr/local/bin/chaos && \
    chmod +x /usr/local/bin/chaos && \
    rm chaos.zip

# Copy Go binaries from the builder stage
RUN mkdir -p /tmp/go-bins
COPY --from=go-builder /go/bin/ /tmp/go-bins/
RUN if [ -n "$(ls -A /tmp/go-bins 2>/dev/null)" ]; then \
      cp -r /tmp/go-bins/* /usr/local/bin/; \
    fi
RUN echo "Checking available binaries:" && ls -la /usr/local/bin/

# Install Sublist3r
RUN git clone https://github.com/aboul3la/Sublist3r.git /opt/Sublist3r || echo "Failed to clone Sublist3r to /opt/Sublist3r"
RUN if [ -d "/opt/Sublist3r" ]; then \
        cd /opt/Sublist3r && \
        pip install -r requirements.txt || echo "Failed to install Sublist3r requirements"; \
    fi

# Also clone Sublist3r to /app/Sublist3r as a backup
RUN git clone https://github.com/aboul3la/Sublist3r.git /app/Sublist3r || echo "Failed to clone Sublist3r to /app/Sublist3r"
RUN if [ -d "/app/Sublist3r" ]; then \
        cd /app/Sublist3r && \
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
