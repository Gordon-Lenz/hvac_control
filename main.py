import configparser
import json
import time
import datetime
import logging
import os
from collections import defaultdict
from gpiozero import OutputDevice
import threading  # Import the threading module

# Import the models from your new file
from models import Base, create_models
from data_generator import DataGenerator
from db_manager import DBManager
from mqtt_manager import MQTTManager  # Import the MQTTManager

# --- Logging Setup ---
# Configure logging to file for errors only with timestamp
logging.basicConfig(filename='hvac_control.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create a console handler for informational messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter for the console handler (with timestamp)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)

# Add the console handler to the root logger
logging.getLogger('').addHandler(console_handler)

# --- Configuration ---
config = configparser.ConfigParser()
config.read('config.ini')

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

# Load relay and sensor mappings from JSON
with open('pin_mappings.json', 'r') as f:
    mappings = json.load(f)

# Get the HVAC unit ID from the config file
hvac_unit_id = config.get('HVAC', 'hvac_unit_id')

# Define the schema name based on the unit ID
schema_name = f'hvac_{hvac_unit_id}'

# --- Database Setup with Error Handling and Environment Variable Fallback---
db_config = config['DATABASE']

# Try to get credentials from environment variables, with fallback to config.ini
db_username = os.environ.get('HVAC_DB_USERNAME', db_config.get('username'))
db_password = os.environ.get('HVAC_DB_PASSWORD', db_config.get('password'))

# Construct the connection string
trusted_connection_str = db_config.get('trusted_connection', 'no').lower()  # Read from config, default to 'no'
if trusted_connection_str == 'yes' or trusted_connection_str == 'true':
    connection_string = f'mssql+pyodbc://{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}&trusted_connection=yes'
else:
    connection_string = f'mssql+pyodbc://{db_username}:{db_password}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}'

# --- Database Manager Setup ---
db_manager = DBManager(connection_string, schema_name, mappings['sensors'])
try:
    db_manager.initialize_db()
except Exception as e:
    logging.error(f"Failed to initialize database: {e}")
    exit(1)

# --- MQTT Setup ---
# Get the MQTT broker address from the config file, with fallback to environment variable
mqtt_broker_address = os.environ.get('MQTT_BROKER_ADDRESS', config.get('MQTT', 'broker_address'))
mqtt_topic = 'hvac/config'
mqtt_manager = MQTTManager('config.ini', mqtt_broker_address, mqtt_topic)
mqtt_manager.connect()

def reload_config_from_file():
    global config, averaging_interval, polling_interval, mqtt_broker_address
    config = load_config()
    averaging_interval = int(config.get('GLOBAL', 'averaging_interval'))
    polling_interval = int(config.get('GLOBAL', 'polling_interval'))
    mqtt_broker_address = config.get('MQTT', 'broker_address')
    logging.info("Configuration reloaded from file.")

mqtt_manager.set_config_reload_callback(reload_config_from_file)

# --- Relay Setup (commented out for now) ---
# relays = {
#     name: OutputDevice(relay['pin'], active_high=True, initial_value=False)
#     for name, relay in relay_mappings.items()
# }

# --- Sensor Setup (commented out for now) ---
# temperature_sensor_pin = sensor_mappings['TEMPERATURE_SENSOR']['pin']
# humidity_sensor_pin = sensor_mappings['HUMIDITY_SENSOR']['pin']

# Initialize sensors based on sensor_mappings and the retrieved pin numbers
# ... (Add your actual sensor initialization code here)

# --- Data Generator Setup ---
data_gen = DataGenerator('pin_mappings.json')

# --- Data Averaging Setup ---
averaging_interval = int(config.get('GLOBAL', 'averaging_interval'))
data_buffer = defaultdict(list)  # Use a defaultdict to store data for averaging
last_db_update_time = time.time()

# --- Main Control Loop ---
try:
    while True:
        # Get other configuration options from the config.ini file
        polling_interval = int(config.get('GLOBAL', 'polling_interval'))

        # Generate and store simulated sensor data
        sensor_readings = data_gen.get_sensor_readings()

        # Add data to the buffer for averaging
        for sensor_name, value in sensor_readings.items():
            data_buffer[sensor_name].append(value)

        current_time = time.time()
        if current_time - last_db_update_time >= averaging_interval:
            # Calculate averages and prepare data for database insertion
            averaged_data = {}
            for sensor_name, values in data_buffer.items():
                # Calculate the average and round to 2 decimal places
                averaged_data[sensor_name] = round(sum(values) / len(values), 2) if values else 0

            # Crucially, use a datetime object here, NOT a string
            averaged_data['timestamp'] = datetime.datetime.now(datetime.timezone.utc)

            # Insert averaged data into the database
            db_manager.insert_sensor_data(averaged_data)

            # Publish averaged data to MQTT (serialize the datetime object here)
            mqtt_topic = f'hvac/{hvac_unit_id}/sensor_data'
            try:
                # Create a copy of the data for MQTT and format the timestamp
                mqtt_data = averaged_data.copy()
                mqtt_data['timestamp'] = mqtt_data['timestamp'].isoformat()

                mqtt_manager.publish(mqtt_topic, mqtt_data)  # Now pass the modified dictionary
                logging.info(f"Published sensor data to MQTT topic: {mqtt_topic}")
            except Exception as e:
                logging.error(f"Failed to publish sensor data to MQTT: {e}")

            # Clear the buffer and update the last update time
            data_buffer.clear()
            last_db_update_time = current_time

        time.sleep(polling_interval)

except KeyboardInterrupt:
    # Cleanup on exit (commented out for now, since relays are not being used)
    # for relay in relays.values():
    #     relay.off()
    print("Exiting...")
finally:
    mqtt_manager.disconnect()