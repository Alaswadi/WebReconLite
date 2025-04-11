# WebReconLite

A lightweight, web-based reconnaissance tool with a cyberpunk UI. WebReconLite performs subdomain enumeration using Subfinder, Assetfinder, Chaos, and Sublist3r, and web detection/probing using Httpx and Gau.

![WebReconLite Screenshot](screenshot.png)

## Features

- **Subdomain Enumeration**: Discover subdomains using multiple tools
- **Web Detection**: Probe hosts to identify live websites, status codes, and titles
- **URL Discovery**: Find endpoints and paths from Common Crawl and Wayback Machine
- **Cyberpunk UI**: Modern, intuitive interface with a hacker aesthetic
- **Concurrent Execution**: Run tools in parallel for faster results
- **Real-time Updates**: See results as they come in

## Prerequisites

Before you can use WebReconLite, you need to install the following tools:

### Subdomain Enumeration Tools

1. **Subfinder**:
   ```
   GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
   ```

2. **Assetfinder**:
   ```
   go install -v github.com/tomnomnom/assetfinder@latest
   ```

3. **Chaos**:
   ```
   GO111MODULE=on go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest
   ```

4. **Sublist3r**:
   ```
   git clone https://github.com/aboul3la/Sublist3r.git
   cd Sublist3r
   pip install -r requirements.txt
   ```

### Web Detection Tools

5. **Httpx**:
   ```
   GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
   ```

6. **Gau**:
   ```
   GO111MODULE=on go install -v github.com/lc/gau/v2/cmd/gau@latest
   ```

Make sure all these tools are in your system PATH.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/WebReconLite.git
   cd WebReconLite
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```

## Usage

1. Start the Flask development server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:8001
   ```

3. Enter a domain (e.g., example.com) and click "Start Scan"

4. View the results in the tabbed interface

## Production Deployment

For production deployment, it's recommended to use Gunicorn with Nginx:

1. Install Gunicorn:
   ```
   pip install gunicorn
   ```

2. Run with Gunicorn:
   ```
   gunicorn -w 4 -b 127.0.0.1:8001 'app:app'
   ```

3. Configure Nginx to proxy requests to Gunicorn

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t webreconlite .
   ```

2. Run the container:
   ```
   docker run -p 8001:8001 webreconlite
   ```

3. Or use Docker Compose:
   ```
   docker-compose up -d
   ```

## Security Considerations

- This tool is intended for legitimate security testing only
- Always ensure you have permission to scan the target domain
- Consider rate limiting to avoid overwhelming target servers
- Do not expose this tool publicly without proper authentication

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by [reconFTW](https://github.com/six2dez/reconftw)
- Thanks to the creators of Subfinder, Assetfinder, Chaos, Sublist3r, Httpx, and Gau
