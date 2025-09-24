#!/bin/bash

# PDF Invoice Parser Web Service - Production Deployment Script
# This script sets up the service for production deployment on a Linux VM

set -e  # Exit on any error

# Configuration
APP_NAME="pdf-parser"
APP_DIR="/opt/pdf-parser"
LOG_DIR="/var/log/pdf-parser"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"
NGINX_SITE="pdf-parser"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    apt update && apt upgrade -y
    log_success "System packages updated"
}

# Install required packages
install_dependencies() {
    log_info "Installing system dependencies..."
    apt install -y python3 python3-pip python3-venv nginx supervisor curl wget git
    log_success "System dependencies installed"
}

# Create application user if not exists
create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        log_info "Creating service user: $SERVICE_USER"
        useradd --system --group --home $APP_DIR --shell /bin/false $SERVICE_USER
        log_success "Service user created"
    else
        log_info "Service user $SERVICE_USER already exists"
    fi
}

# Create directories
create_directories() {
    log_info "Creating application directories..."
    
    mkdir -p $APP_DIR
    mkdir -p $LOG_DIR
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP $APP_DIR
    chown -R $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
    chmod 755 $APP_DIR
    chmod 755 $LOG_DIR
    
    log_success "Directories created and permissions set"
}

# Copy application files
deploy_application() {
    log_info "Deploying application files..."
    
    # Copy all Python files
    cp *.py $APP_DIR/
    cp requirements.txt $APP_DIR/
    cp gunicorn.conf.py $APP_DIR/
    cp index.html $APP_DIR/
    
    # Copy any test PDFs for testing
    if [ -f "invoice-act.pdf" ]; then
        cp invoice-act.pdf $APP_DIR/
    fi
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_GROUP $APP_DIR
    chmod +x $APP_DIR/*.py
    
    log_success "Application files deployed"
}

# Setup Python virtual environment
setup_virtualenv() {
    log_info "Setting up Python virtual environment..."
    
    cd $APP_DIR
    sudo -u $SERVICE_USER python3 -m venv venv
    sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install -r requirements.txt
    
    log_success "Virtual environment created and dependencies installed"
}

# Install systemd service
install_service() {
    log_info "Installing systemd service..."
    
    cp pdf-parser.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable pdf-parser.service
    
    log_success "Systemd service installed and enabled"
}

# Configure nginx
configure_nginx() {
    log_info "Configuring nginx..."
    
    # Copy nginx configuration
    cp nginx-pdf-parser.conf /etc/nginx/sites-available/$NGINX_SITE
    
    # Enable site
    ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    log_success "Nginx configured and reloaded"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start PDF parser service
    systemctl start pdf-parser.service
    
    # Enable and start nginx if not running
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Services started"
}

# Check service status
check_status() {
    log_info "Checking service status..."
    
    echo "PDF Parser Service Status:"
    systemctl status pdf-parser.service --no-pager
    
    echo -e "\nNginx Status:"
    systemctl status nginx --no-pager
    
    echo -e "\nService URLs:"
    echo "  Frontend: http://localhost/"
    echo "  API: http://localhost/api/v1/"
    echo "  Health Check: http://localhost/health"
    
    # Test API health
    log_info "Testing API health..."
    sleep 5  # Give services time to start
    
    if curl -f http://localhost/health >/dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_warning "API health check failed - check logs"
        echo "  Check logs: journalctl -u pdf-parser.service -f"
        echo "  Error logs: tail -f $LOG_DIR/error.log"
    fi
}

# Create logrotate configuration
setup_logrotate() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/pdf-parser << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload pdf-parser.service
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Main deployment function
main() {
    echo "==============================================="
    echo "PDF Invoice Parser - Production Deployment"
    echo "==============================================="
    
    check_root
    
    log_info "Starting deployment process..."
    
    update_system
    install_dependencies
    create_user
    create_directories
    deploy_application
    setup_virtualenv
    install_service
    configure_nginx
    setup_logrotate
    start_services
    check_status
    
    echo "==============================================="
    log_success "Deployment completed successfully!"
    echo "==============================================="
    
    echo "Next steps:"
    echo "1. Update server_name in /etc/nginx/sites-available/$NGINX_SITE"
    echo "2. Configure SSL certificates for HTTPS (recommended)"
    echo "3. Configure firewall to allow HTTP/HTTPS traffic"
    echo "4. Test the application with a sample PDF"
    echo ""
    echo "Useful commands:"
    echo "  View logs: journalctl -u pdf-parser.service -f"
    echo "  Restart service: systemctl restart pdf-parser.service"
    echo "  Check status: systemctl status pdf-parser.service"
    echo "  Test API: curl http://localhost/api/v1/health"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi