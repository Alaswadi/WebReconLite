#!/bin/bash

# WebReconLite Docker Helper Script

# Function to display help
show_help() {
    echo "WebReconLite Docker Helper Script"
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  start       Start the Docker container"
    echo "  stop        Stop the Docker container"
    echo "  restart     Restart the Docker container"
    echo "  logs        Show container logs"
    echo "  status      Check container status"
    echo "  tools       Check which tools are installed"
    echo "  help        Show this help message"
    echo ""
}

# Function to build the Docker image
build_image() {
    echo "Building WebReconLite Docker image..."
    docker-compose build
}

# Function to start the container
start_container() {
    echo "Starting WebReconLite container..."
    docker-compose up -d
    echo "WebReconLite is now running at http://localhost:8001"
}

# Function to stop the container
stop_container() {
    echo "Stopping WebReconLite container..."
    docker-compose down
}

# Function to restart the container
restart_container() {
    echo "Restarting WebReconLite container..."
    docker-compose restart
}

# Function to show container logs
show_logs() {
    echo "Showing WebReconLite container logs..."
    docker-compose logs -f
}

# Function to check container status
check_status() {
    echo "Checking WebReconLite container status..."
    docker-compose ps
}

# Function to check which tools are installed
check_tools() {
    echo "Checking which tools are installed in the container..."
    docker-compose exec webreconlite /usr/local/bin/check-tools.sh
}

# Main script logic
case "$1" in
    build)
        build_image
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    status)
        check_status
        ;;
    tools)
        check_tools
        ;;
    help|*)
        show_help
        ;;
esac
