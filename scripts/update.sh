#!/bin/bash

# --- Script Start ---

echo "Starting HVAC Control Project Update..."

# Navigate to the project directory
cd /home/pi/hvac_control || { echo "Error: Project directory not found."; exit 1; }

# Stop the systemd service
echo "Stopping HVAC Control service..."
sudo systemctl stop hvac_control.service

# Pull the latest changes from the repository
echo "Updating the project from the repository..."
git pull origin main

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update Python dependencies
echo "Updating Python dependencies..."
pip install --no-cache-dir -r requirements.txt --upgrade

# --- Update authorized_keys (if needed) ---
# Check if authorized_keys directory exists
if [ ! -d /home/pi/hvac_control/install/authorized_keys ]; then
  echo "Warning: authorized_keys directory not found. SSH keys will not be updated."
else
  # Clear the existing authorized_keys file
  echo "Updating SSH authorized keys..."
  > /home/pi/.ssh/authorized_keys

  # Loop through all files in the authorized_keys directory
  while IFS= read -r -d $'\0' pubkey_file; do
    if [[ "$pubkey_file" =~ \.pub$ ]]; then
      echo "  Adding key from: $pubkey_file"
      cat "$pubkey_file" >> /home/pi/.ssh/authorized_keys
    else
      echo "  Skipping non .pub file: $pubkey_file"
    fi
  done < <(find /home/pi/hvac_control/install/authorized_keys -type f -print0)

  # Set correct permissions on the authorized_keys file
  chmod 600 /home/pi/.ssh/authorized_keys
  chown pi:pi /home/pi/.ssh/authorized_keys

  echo "SSH authorized keys updated."
fi

# --- Restart the systemd Service ---
echo "Restarting HVAC Control service..."
sudo systemctl daemon-reload
sudo systemctl start hvac_control.service

echo "HVAC Control Project update completed."

# --- Script End ---
