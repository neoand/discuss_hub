#!/bin/bash
###############################################################################
# DiscussHub - Production Installation Script
# Version: 1.0.0
# Odoo: 18.0
# Date: October 18, 2025
#
# This script automates the installation of DiscussHub on an active Odoo 18
# production instance.
#
# Usage:
#   sudo ./install_discuss_hub.sh [database_name] [addons_path]
#
# Example:
#   sudo ./install_discuss_hub.sh my_production_db /opt/odoo/custom_addons
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   ${GREEN}DiscussHub Installation Script${NC}                   ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}   Version 18.0.4.0.0                                ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root or with sudo"
    exit 1
fi

# Parse arguments
DB_NAME=${1:-""}
ADDONS_PATH=${2:-"/opt/odoo/custom_addons"}

print_header

# Validation
if [ -z "$DB_NAME" ]; then
    print_error "Database name required"
    echo "Usage: sudo $0 [database_name] [addons_path]"
    echo "Example: sudo $0 my_production_db /opt/odoo/custom_addons"
    exit 1
fi

print_step "Configuration:"
echo "  Database: $DB_NAME"
echo "  Addons Path: $ADDONS_PATH"
echo ""

# Confirmation
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Installation cancelled"
    exit 0
fi

# Step 1: Backup
print_step "Step 1: Creating backup..."
BACKUP_DIR="/backup/discuss_hub_install_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
print_step "Backing up database..."
sudo -u postgres pg_dump -F c -b -v -f "$BACKUP_DIR/database.backup" $DB_NAME
if [ $? -eq 0 ]; then
    print_success "Database backed up to $BACKUP_DIR/database.backup"
else
    print_error "Database backup failed"
    exit 1
fi

# Step 2: Install Python dependencies
print_step "Step 2: Installing Python dependencies..."

# Detect Python version used by Odoo
PYTHON_BIN=$(which python3)
print_step "Using Python: $PYTHON_BIN"

$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install google-generativeai textblob SpeechRecognition pydub Pillow

if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Download TextBlob corpora
print_step "Downloading TextBlob corpora..."
$PYTHON_BIN -m textblob.download_corpora 2>&1 | grep -v "already installed" || true
print_success "TextBlob corpora ready"

# Step 3: Clone/Copy DiscussHub
print_step "Step 3: Installing DiscussHub modules..."

cd $ADDONS_PATH

if [ -d "discuss_hub" ]; then
    print_warning "discuss_hub directory already exists"
    read -p "Update existing installation? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Updating via git pull..."
        cd discuss_hub
        git pull
        cd ..
    else
        print_warning "Skipping directory creation"
    fi
else
    print_step "Cloning from GitHub..."
    git clone https://github.com/neoand/discuss_hub.git discuss_hub_temp

    # Move modules to addons path
    mv discuss_hub_temp/community_addons/discuss_hub ./
    mv discuss_hub_temp/community_addons/discusshub_crm ./
    mv discuss_hub_temp/community_addons/discusshub_helpdesk ./
    mv discuss_hub_temp/community_addons/discusshub_project ./

    # Cleanup
    rm -rf discuss_hub_temp

    print_success "DiscussHub modules copied"
fi

# Set permissions
print_step "Setting permissions..."
chown -R odoo:odoo discuss_hub*
chmod -R 755 discuss_hub*
print_success "Permissions set"

# Step 4: Install module in Odoo
print_step "Step 4: Installing module in Odoo..."

# Check if Odoo is running
if systemctl is-active --quiet odoo; then
    ODOO_WAS_RUNNING=true
    print_step "Stopping Odoo..."
    systemctl stop odoo
else
    ODOO_WAS_RUNNING=false
fi

# Install module
print_step "Installing discuss_hub module..."
sudo -u odoo /usr/bin/odoo \
    -c /etc/odoo/odoo.conf \
    -d $DB_NAME \
    -i discuss_hub \
    --stop-after-init \
    --log-level=info

if [ $? -eq 0 ]; then
    print_success "Module installed successfully"
else
    print_error "Module installation failed"
    print_warning "Check logs at /var/log/odoo/odoo.log"

    # Restart Odoo if it was running
    if [ "$ODOO_WAS_RUNNING" = true ]; then
        systemctl start odoo
    fi
    exit 1
fi

# Restart Odoo
if [ "$ODOO_WAS_RUNNING" = true ]; then
    print_step "Starting Odoo..."
    systemctl start odoo
    sleep 3

    if systemctl is-active --quiet odoo; then
        print_success "Odoo restarted successfully"
    else
        print_error "Odoo failed to start - check logs"
        exit 1
    fi
fi

# Step 5: Verification
print_step "Step 5: Verification..."

# Check if module is installed
sudo -u postgres psql -d $DB_NAME -t -c \
    "SELECT COUNT(*) FROM ir_module_module WHERE name='discuss_hub' AND state='installed';" | grep -q "1"

if [ $? -eq 0 ]; then
    print_success "Module verified as installed in database"
else
    print_error "Module not found in database"
    exit 1
fi

# Final summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}   ${GREEN}✓ Installation Completed Successfully!${NC}            ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Login to Odoo as administrator"
echo "  2. Go to: Discuss Hub → Connectors"
echo "  3. Create your first connector (WhatsApp or Telegram)"
echo "  4. Configure AI Responder (optional)"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Documentation: https://github.com/neoand/discuss_hub/tree/main/community_addons/discuss_hub/docs"
echo ""
print_success "Installation complete! 🎉"
