FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    golang \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment variables
ENV GOPATH /root/go
ENV PATH $PATH:/root/go/bin

# Install reconnaissance tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/tomnomnom/assetfinder@latest && \
    go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest

# Install Sublist3r
RUN git clone https://github.com/aboul3la/Sublist3r.git /opt/Sublist3r && \
    cd /opt/Sublist3r && \
    pip install -r requirements.txt

# Add Sublist3r to PATH
ENV PATH $PATH:/opt/Sublist3r

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

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "app:app"]
