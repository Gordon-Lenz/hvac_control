#!/bin/bash

# --- Script Start ---

echo "Starting HVAC Control Project Installation..."

# --- Prompt for User Input ---
read -p "Enter your SQL Server address: " sql_server_address
read -p "Enter your SQL Server username: " sql_username
read -s -p "Enter your SQL Server password: " sql_password
echo  # Add a newline after the password prompt
read -p "Enter your HVAC unit ID: " hvac_unit_id
read -p "Enter your MQTT broker address: " mqtt_broker_address
read -p "Enter your MQTT username: " mqtt_username
read -s -p "Enter your MQTT password: " mqtt_password
echo  # Add a newline after the password prompt

# --- Update System ---
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# --- Install Required System Packages ---
echo "Installing required system packages (ODBC driver, etc.)..."
sudo apt-get install -y --no-install-recommends \
    unixodbc unixodbc-dev odbcinst odbcinst1debian2 libodbc1 \
    curl git python3 python3-pip python3-venv

# --- Install Microsoft ODBC Driver 17 for SQL Server ---
echo "Installing Microsoft ODBC Driver 17 for SQL Server..."
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17

# --- Clone the Repository ---
echo "Cloning the project repository..."
git clone https://github.com/Gordon-Lenz/hvac_control /home/pi/hvac_control
cd /home/pi/hvac_control

# --- Create and Activate a Virtual Environment ---
echo "Creating a virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# --- Install Python Dependencies ---
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# --- Configure SQL Server (if applicable) ---
# Note: This section assumes SQL Server is already installed and configured on a remote machine.
#       You may need to adjust these steps if you are installing SQL Server locally on the Raspberry Pi.
echo "Skipping SQL Server installation (assuming remote server)."

# --- Configure config.ini ---
echo "Configuring config.ini..."
# Database Settings
sed -i "s|localhost\\\\SQLEXPRESS|$sql_server_address|g" config.ini
sed -i "s|hvac_admin|$sql_username|g" config.ini
sed -i "s|p|$sql_password|g" config.ini

# HVAC Unit ID
sed -i "s|uno|$hvac_unit_id|g" config.ini

# MQTT Broker Address
sed -i "s|localhost|$mqtt_broker_address|g" config.ini

# --- Configure Environment Variables ---
echo "Setting environment variables..."
echo "export HVAC_DB_USERNAME=$sql_username" >> /home/pi/.bashrc
echo "export HVAC_DB_PASSWORD=$sql_password" >> /home/pi/.bashrc
echo "export MQTT_BROKER_ADDRESS=$mqtt_broker_address" >> /home/pi/.bashrc
echo "export MQTT_USERNAME=$mqtt_username" >> /home/pi/.bashrc
echo "export MQTT_PASSWORD=$mqtt_password" >> /home/pi/.bashrc
source /home/pi/.bashrc

# --- Configure Mosquitto MQTT Broker (Optional) ---
echo "Installing and configuring Mosquitto MQTT Broker (Optional)..."
sudo apt-get install -y mosquitto mosquitto-clients

# Create a Mosquitto password file
# Use the entered MQTT username for Mosquitto setup
sudo mosquitto_passwd -c /etc/mosquitto/passwd $mqtt_username

# Configure Mosquitto to use the password file
sudo tee /etc/mosquitto/conf.d/default.conf <<EOF
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

# Restart Mosquitto
sudo systemctl restart mosquitto

# --- Configure pin_mappings.json (Optional) ---
# Note: If you are using physical sensors and relays, update pin_mappings.json to match your wiring.
echo "Skipping pin_mappings.json configuration (update manually if needed)."

# --- SSH Setup ---
echo "Setting up SSH..."

# Install OpenSSH server if it's not already installed
if ! dpkg -l | grep -q openssh-server; then
  echo "Installing OpenSSH server..."
  sudo apt-get install -y openssh-server
fi

# Enable and start the SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# Configure SSH for key-based authentication
echo "Setting up SSH key-based authentication..."
mkdir -p /home/pi/.ssh

# --- Copy Public Keys from Directory ---
# **Corrected the path to the authorized_keys directory**
if [ ! -d /home/pi/hvac_control/install/authorized_keys ]; then
  echo "Error: authorized_keys directory not found in the installation directory."
  exit 1
fi

# Loop through all files in the authorized_keys directory
echo "Copying public keys from authorized_keys directory..."
while IFS= read -r -d $'\0' pubkey_file; do
  if [[ "$pubkey_file" =~ \.pub$ ]]; then  # Check if it's a .pub file
    echo "  Adding key from: $pubkey_file"
    cat "$pubkey_file" >> /home/pi/.ssh/authorized_keys
  else
    echo "  Skipping non .pub file: $pubkey_file"
  fi
done < <(find /home/pi/hvac_control/install/authorized_keys -type f -print0)

# Set correct permissions on the authorized_keys file
chmod 600 /home/pi/.ssh/authorized_keys
chown pi:pi /home/pi/.ssh/authorized_keys

echo "SSH key-based authentication configured."

# --- Create systemd Service ---
echo "Creating systemd service..."
sudo tee /etc/systemd/system/hvac_control.service <<EOF
[Unit]
Description=HVAC Control Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/hvac_control
ExecStart=/home/pi/hvac_control/.venv/bin/python /home/pi/hvac_control/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# --- Enable and Start the systemd Service ---
sudo systemctl daemon-reload
sudo systemctl enable hvac_control.service
sudo systemctl start hvac_control.service

echo "systemd service created and started."

# --- Run the Application ---
# Note: The application is now managed by systemd, so we don't need to start it here.
# echo "Installation complete. Starting the application..."
# python main.py

echo "HVAC Control Project installation and startup completed."

# --- Script End ---
