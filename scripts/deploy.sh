#!/bin/bash

# Deployment script for MedusaXD AI Image Editor Bot

set -e  # Exit on any error

echo "🚀 MedusaXD AI Image Editor Bot Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_status "Creating .env from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your actual values before continuing."
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("TELEGRAM_BOT_TOKEN" "BFL_API_KEY" "MONGODB_URL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

print_success "Environment validation passed"

# Function to deploy with Docker
deploy_docker() {
    print_status "Deploying with Docker..."
    
    # Build the image
    print_status "Building Docker image..."
    docker build -t medusaxd-ai-bot .
    
    # Stop existing container if running
    if [ "$(docker ps -q -f name=medusaxd-ai-bot)" ]; then
        print_status "Stopping existing container..."
        docker stop medusaxd-ai-bot
        docker rm medusaxd-ai-bot
    fi
    
    # Run the container
    print_status "Starting new container..."
    docker run -d \
        --name medusaxd-ai-bot \
        --restart unless-stopped \
        --env-file .env \
        -v $(pwd)/logs:/app/logs \
        medusaxd-ai-bot
    
    print_success "Docker deployment completed"
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose down
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker Compose deployment completed"
    else
        print_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
}

# Function to deploy to Render.com
deploy_render() {
    print_status "Preparing for Render.com deployment..."
    
    # Check if render.yaml exists
    if [ ! -f render.yaml ]; then
        print_error "render.yaml not found!"
        exit 1
    fi
    
    # Check if git repository is clean
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Git repository has uncommitted changes"
        read -p "Do you want to commit and push changes? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
            git push origin main
        else
            print_error "Please commit your changes before deploying to Render.com"
            exit 1
        fi
    fi
    
    print_success "Ready for Render.com deployment"
    print_status "Please follow these steps:"
    echo "1. Go to https://render.com"
    echo "2. Connect your GitHub repository"
    echo "3. Create a new Background Worker service"
    echo "4. Set the following environment variables in Render dashboard:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - BFL_API_KEY"
    echo "   - MONGODB_URL"
    echo "   - ADMIN_USER_IDS (optional)"
    echo "5. Deploy the service"
}

# Function to run locally
run_local() {
    print_status "Running bot locally..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    # Run the bot
    print_status "Starting bot..."
    python main.py
}

# Main deployment logic
case "${1:-local}" in
    "docker")
        deploy_docker
        ;;
    "compose")
        deploy_docker_compose
        ;;
    "render")
        deploy_render
        ;;
    "local")
        run_local
        ;;
    *)
        echo "Usage: $0 [local|docker|compose|render]"
        echo ""
        echo "Deployment options:"
        echo "  local   - Run locally with virtual environment"
        echo "  docker  - Deploy with Docker"
        echo "  compose - Deploy with Docker Compose"
        echo "  render  - Prepare for Render.com deployment"
        exit 1
        ;;
esac

print_success "Deployment script completed!"
