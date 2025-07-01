#!/bin/bash

# Setup script for MedusaXD AI Image Editor Bot

set -e  # Exit on any error

echo "🎨 MedusaXD AI Image Editor Bot Setup"
echo "===================================="

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

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        required_version="3.8"
        
        if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
            print_success "Python $python_version found"
        else
            print_error "Python $required_version or higher is required. Found: $python_version"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip..."
    
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 is not installed"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            print_status "Using existing virtual environment"
            return
        fi
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create environment file
create_env_file() {
    print_status "Setting up environment file..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        return
    fi
    
    cp .env.example .env
    print_success ".env file created from template"
    
    print_warning "Please edit .env file with your actual values:"
    echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather)"
    echo "  - BFL_API_KEY (get from https://bfl.ai)"
    echo "  - MONGODB_URL (your MongoDB connection string)"
    echo "  - ADMIN_USER_IDS (optional, comma-separated)"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p temp
    
    print_success "Directories created"
}

# Setup git hooks (optional)
setup_git_hooks() {
    if [ -d ".git" ]; then
        print_status "Setting up git hooks..."
        
        # Pre-commit hook for code formatting
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for MedusaXD Bot

echo "Running pre-commit checks..."

# Check if black is available
if command -v black &> /dev/null; then
    echo "Formatting code with black..."
    black src/ --check --diff
    if [ $? -ne 0 ]; then
        echo "Code formatting issues found. Run 'black src/' to fix."
        exit 1
    fi
fi

# Check if flake8 is available
if command -v flake8 &> /dev/null; then
    echo "Running flake8 linting..."
    flake8 src/ --max-line-length=100 --ignore=E203,W503
    if [ $? -ne 0 ]; then
        echo "Linting issues found. Please fix them."
        exit 1
    fi
fi

echo "Pre-commit checks passed!"
EOF
        
        chmod +x .git/hooks/pre-commit
        print_success "Git hooks setup completed"
    fi
}

# Validate setup
validate_setup() {
    print_status "Validating setup..."
    
    # Check if .env file has required variables
    if [ -f ".env" ]; then
        source .env
        
        if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
            print_warning "TELEGRAM_BOT_TOKEN not set in .env file"
        fi
        
        if [ -z "$BFL_API_KEY" ] || [ "$BFL_API_KEY" = "your_bfl_api_key_here" ]; then
            print_warning "BFL_API_KEY not set in .env file"
        fi
        
        if [ -z "$MONGODB_URL" ] || [ "$MONGODB_URL" = "mongodb+srv://username:password@cluster.mongodb.net/medusaxd_bot?retryWrites=true&w=majority" ]; then
            print_warning "MONGODB_URL not set in .env file"
        fi
    fi
    
    print_success "Setup validation completed"
}

# Main setup process
main() {
    print_status "Starting MedusaXD AI Image Editor Bot setup..."
    
    check_python
    check_pip
    create_venv
    install_dependencies
    create_env_file
    create_directories
    setup_git_hooks
    validate_setup
    
    print_success "Setup completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Edit .env file with your actual API keys and database URL"
    echo "2. Run the bot with: ./scripts/deploy.sh local"
    echo "3. Or deploy with Docker: ./scripts/deploy.sh docker"
    echo ""
    print_status "For help, run: python main.py --help"
}

# Run main function
main
