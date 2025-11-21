#!/bin/bash

# AI Sales Assistant - Docker Run Script
# This script provides easy commands to build and run the Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
}

# Build the Docker image
build_image() {
    print_info "Building Docker image..."
    docker build -t ai-sales-assistant .
    print_success "Docker image built successfully!"
}

# Run the container
run_container() {
    print_info "Starting AI Sales Assistant container..."

    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f .env.docker ]; then
            cp .env.docker .env
            print_warning "Please edit .env file with your actual API keys before running!"
            print_info "Required: GEMINI_API_KEY and SECRET_KEY"
        else
            print_error ".env.docker template not found!"
            exit 1
        fi
    fi

    # Run the container
    docker run -d \
        --name ai-sales-assistant \
        -p 5050:5050 \
        --env-file .env \
        -v "$(pwd)/DataFile_students_OPTIMIZED.xlsx:/app/DataFile_students_OPTIMIZED.xlsx:ro" \
        -v "ai-sales-uploads:/app/uploads" \
        -v "ai-sales-output:/app/output" \
        ai-sales-assistant

    print_success "Container started successfully!"
    print_info "Web interface: http://localhost:5050"
    print_info "Health check: http://localhost:5050/api/health"
}

# Stop the container
stop_container() {
    print_info "Stopping AI Sales Assistant container..."
    docker stop ai-sales-assistant 2>/dev/null || true
    docker rm ai-sales-assistant 2>/dev/null || true
    print_success "Container stopped and removed."
}

# Show logs
show_logs() {
    print_info "Showing container logs..."
    docker logs -f ai-sales-assistant
}

# Show status
show_status() {
    print_info "Container status:"
    docker ps -f name=ai-sales-assistant --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    if docker ps -f name=ai-sales-assistant -q | grep -q .; then
        print_success "Container is running!"
        print_info "Health check: curl http://localhost:5050/api/health"
    else
        print_warning "Container is not running."
    fi
}

# Clean up
cleanup() {
    print_info "Cleaning up Docker resources..."
    docker stop ai-sales-assistant 2>/dev/null || true
    docker rm ai-sales-assistant 2>/dev/null || true
    docker rmi ai-sales-assistant 2>/dev/null || true
    docker volume rm ai-sales-uploads ai-sales-output 2>/dev/null || true
    print_success "Cleanup completed."
}

# Main menu
show_help() {
    echo "AI Sales Assistant - Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     - Build the Docker image"
    echo "  run       - Run the container"
    echo "  stop      - Stop and remove the container"
    echo "  logs      - Show container logs"
    echo "  status    - Show container status"
    echo "  restart   - Restart the container"
    echo "  cleanup   - Remove container, image, and volumes"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build run    # Build and run"
    echo "  $0 stop         # Stop the container"
    echo "  $0 logs         # View logs"
}

# Main logic
main() {
    check_docker

    case "${1:-help}" in
        build)
            build_image
            ;;
        run)
            if [ "$2" = "build" ]; then
                build_image
            fi
            run_container
            ;;
        stop)
            stop_container
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        restart)
            stop_container
            sleep 2
            run_container
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
