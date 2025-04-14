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
    echo "  flower      Open Flower monitoring UI in browser"
    echo "  celery      Show Celery worker logs"
    echo "  testdb      Test the database functionality"
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
    echo "Flower monitoring is available at http://localhost:5555"
    echo "Use './run.sh flower' to open Flower in your browser"
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

# Function to open Flower monitoring UI in browser
open_flower() {
    echo "Opening Flower monitoring UI in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:5555
    elif command -v open &> /dev/null; then
        open http://localhost:5555
    elif command -v start &> /dev/null; then
        start http://localhost:5555
    else
        echo "Could not open browser automatically. Please visit http://localhost:5555 manually."
    fi
}

# Function to show Celery worker logs
show_celery_logs() {
    echo "Showing Celery worker logs..."
    docker-compose logs -f celery-worker
}

# Function to test the database functionality
test_database() {
    echo "Testing database functionality..."
    docker-compose exec webreconlite python test_db.py
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
    flower)
        open_flower
        ;;
    celery)
        show_celery_logs
        ;;
    testdb)
        test_database
        ;;
    help|*)
        show_help
        ;;
esac
