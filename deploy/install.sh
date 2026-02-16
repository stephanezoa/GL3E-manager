#!/bin/bash
set -e

# Update usage
echo "Updating GL3E Project Assignment System..."

# Install dependencies if not present
if ! command -v nginx &> /dev/null; then
    echo "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y nginx certbot python3-certbot-nginx python3-venv sqlite3
fi

# Create virtualenv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create static directory if not exists
mkdir -p static/css static/js static/img

# Initialize database
echo "Initializing database..."
python init_db.py

# Set permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data .
sudo chmod -R 755 .
sudo chmod 664 gl3e_assignments.db

# Deployment actions
echo "Restarting services..."
if [ -f "/etc/systemd/system/gl3e-assignment.service" ]; then
    sudo systemctl restart gl3e-assignment
else
    echo "Service not installed. Please copy service file first."
fi

echo "Deployment complete!"
