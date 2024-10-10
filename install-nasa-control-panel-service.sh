#!/bin/bash

# NASA Control Panel Service Installer

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root or using sudo."
    exit 1
fi

# Configuration
SERVICE_NAME="nasa-control-panel"
PYTHON_SCRIPT_PATH="/path/to/your/start_mission_control.py"
WORKING_DIR="/path/to/your/nasa_control_panel_directory"
USER="your_username"
GROUP="your_usergroup"

# Prompt for configuration
read -p "Enter the full path to start_mission_control.py: " PYTHON_SCRIPT_PATH
read -p "Enter the working directory: " WORKING_DIR
read -p "Enter the user to run the service: " USER
read -p "Enter the group to run the service: " GROUP

# Create the service file
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=NASA Control Panel Simulation
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT_PATH
WorkingDirectory=$WORKING_DIR
User=$USER
Group=$GROUP
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd manager configuration
systemctl daemon-reload

# Enable the service
systemctl enable $SERVICE_NAME.service

# Start the service
systemctl start $SERVICE_NAME.service

# Check the status
systemctl status $SERVICE_NAME.service

echo "NASA Control Panel service has been installed and started."
echo "You can manage it using: sudo systemctl [start|stop|restart|status] $SERVICE_NAME.service"
echo "To view logs, use: sudo journalctl -u $SERVICE_NAME.service"
