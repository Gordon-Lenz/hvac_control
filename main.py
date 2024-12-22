import configparser
import json
import time
import datetime
import threading
import logging
import asyncio
from gpiozero import OutputDevice
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
import shelve
from asyncio_mqtt import Client

# Import the models from your new file
from models import Base, create_models

# Import the decorators
from shared.decorators import log_exceptions, retry_on_failure

# Import the simulation function
from simulation import simulate_sensor_data

# Import the MQTT client functions
from mqtt_client import create_mqtt_client, publish_sensor_data

# --- Logging Setup ---
# Configure logging to file for errors only with timestamp
logging.basicConfig(filename='hvac_control.log', level=logging.ERROR,
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

# Load relay and sensor mappings from JSON
with open('pin_mappings.json', 'r') as f:
   mappings = json.load(f)

hvac_unit_id = config.get('HVAC', 'hvac_unit_id')  # Define hvac_unit_id here

# Define the schema name based on the unit ID
schema_name = f'hvac_{hvac_unit_id}'

# --- Helper Functions ---
@log_exceptions
@retry_on_failure(max_retries=3, delay=5)
def create_database_engine(connection_string, schema_name):
    """
    Creates a SQLAlchemy engine and ensures the schema exists.
    """
    try:
        engine = create_engine(connection_string)

        with engine.connect() as connection:
            if not engine.dialect.has_schema(connection, schema_name):
                connection.execute(CreateSchema(schema_name))

        return engine

    except OperationalError as e:
        print(f"Error connecting to the database or creating schema: {e}")
        exit(1)

@log_exceptions
def create_database_session(engine):
    """
    Creates a SQLAlchemy session factory.
    """
    return sessionmaker(bind=engine)

# --- Database Setup with Error Handling ---
db_config = config['DATABASE']

# Construct the connection string
connection_string = f'mssql+pyodbc://{db_config["username"]}:{db_config["password"]}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}&trusted_connection=yes'

# Create the database engine and session factory
engine = create_database_engine(connection_string, schema_name)
Session = create_database_session(engine)

# Create the models with dynamic table names and columns
HvacSensorData, HvacConfig = create_models(schema_name, mappings['sensors'])

# Create the database tables within the specified schema (if they don't exist)
Base.metadata.create_all(engine)

# --- Reconcile config.ini with Database ---
@log_exceptions
@retry_on_failure(max_retries=3, delay=5)
def reconcile_config_with_db(config, engine, HvacConfig):
    """
    Reconciles the config.ini file with the database.
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    for section in config.sections():
        for option in config.options(section):
            db_config_option = session.query(HvacConfig).filter_by(section=section, option=option).first()
            if db_config_option:
                # Option exists in the database, compare values
                if db_config_option.value != config.get(section, option):
                    # Update config.ini with the value from the database
                    config.set(section, option, db_config_option.value)
                    db_config_option.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    logging.info(f"Updated '{option}' in section '{section}' from database.")
            else:
                # Option doesn't exist in the database, add it
                new_config = HvacConfig(section=section, option=option, value=config.get(section, option))
                session.add(new_config)
                logging.info(f"Added '{option}' in section '{section}' to database.")
    
    session.commit()
    session.close()

reconcile_config_with_db(config, engine, HvacConfig)

# Write the updated config back to config.ini
with open('config.ini', 'w') as configfile:
    config.write(configfile)

# --- Relay Setup ---
relays = {
    name: OutputDevice(relay['pin'], active_high=True, initial_value=False)
    for name, relay in mappings['relays'].items()
}

# --- Sensor Data Class ---
class SensorData:
    def __init__(self, sensor_mappings, **kwargs):
        """
        Initializes the SensorData object with sensor readings from kwargs.
        """
        self.sensor_mappings = sensor_mappings
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        for sensor_name in sensor_mappings:
            setattr(self, sensor_name, kwargs.get(sensor_name))

    def to_dict(self):
        """
        Returns a dictionary representation of the sensor data, 
        including descriptions from sensor_mappings.
        """
        data_dict = {'timestamp': self.timestamp}
        for sensor_name, sensor_info in self.sensor_mappings.items():
            data_dict[sensor_name] = getattr(self, sensor_name)
            # Include the description in the dictionary
            data_dict[f'{sensor_name}_description'] = sensor_info.get('description')  
        return data_dict

    def get_database_data(self):
        """
        Returns a dictionary with only the data to be stored in the database.
        """
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "timestamp": self.timestamp
        }

    def get_mqtt_data(self):
        """
        Returns a dictionary with all sensor data and relay statuses for MQTT.
        """
        mqtt_data = self.to_dict()  # Start with all sensor data
        # Add relay statuses
        for relay_name, relay in relays.items():
            mqtt_data[f'relay_{relay_name}'] = relay.is_active
        return mqtt_data

# --- Function to insert sensor data into the database in a separate thread ---
@log_exceptions
def insert_sensor_data_db(sensor_data):
    """
    Inserts sensor data into the database in a separate thread.
    """
    Session = sessionmaker(bind=engine)
    with Session() as session:
        try:
            new_sensor_data = HvacSensorData(**sensor_data.get_database_data())
            session.add(new_sensor_data)
            session.commit()
            logging.info("Sensor data inserted into the database.")
        except Exception as e:
            session.rollback()
            logging.error(f"Error inserting sensor data: {e}")

# --- Persistent Cache for Setpoints ---
setpoint_cache_file = 'setpoint_cache.db'  # Choose a filename for your cache

@log_exceptions
def open_setpoint_cache(filename):
    """
    Opens the persistent setpoint cache using shelve.
    """
    try:
        return shelve.open(filename)
    except Exception as e:
        logging.error(f"Error opening setpoint cache file: {e}")
        raise  # Re-raise the exception to be handled elsewhere

@log_exceptions
def update_setpoint_cache(cache, setpoints):
    """
    Updates the setpoint cache with new values.
    """
    cache['setpoints'] = setpoints
    cache.sync()

@log_exceptions
def get_setpoints_from_cache(cache):
    """
    Retrieves setpoints from the cache.
    """
    if 'setpoints' in cache:
        return cache['setpoints']
    return None  # Or return default setpoints

async def read_and_publish_sensor_data(polling_interval):
    """Reads sensor data, publishes it to MQTT, and stores it in the database."""

    # Open the setpoint cache
    setpoint_cache = open_setpoint_cache(setpoint_cache_file)

    while True:
        # Get other configuration options from the config.ini file
        default_temperature = float(config.get('HVAC', 'default_temperature'))

        # 2. Read sensor data (or use simulated data for now)
        simulated_sensor_data = simulate_sensor_data(mappings['sensors'])
        print(f"Simulated sensor readings: {simulated_sensor_data}")

        # Create a SensorData object
        sensor_data = SensorData(mappings['sensors'], **simulated_sensor_data)

        # 3. Implement your HVAC control logic (example)
        if sensor_data.temperature < default_temperature:
            relays['HVAC_POWER'].on()
        else:
            relays['HVAC_POWER'].off()

        # Publish ALL sensor data and relay status to MQTT
        try:
            await mqtt_client.publish(f"hvac/{hvac_unit_id}/sensor_data", json.dumps(sensor_data.get_mqtt_data()))
        except Exception as e:
            logging.error(f"Error publishing to MQTT: {e}")

        # 4. Store sensor data in the database (in a separate thread)
        threading.Thread(target=insert_sensor_data_db, args=(sensor_data,), daemon=True).start()

        """ # Update setpoint cache (example, assuming you receive setpoints from MQTT)
        try:
            # ... (receive setpoints from MQTT - use asyncio_helper here)
            update_setpoint_cache(setpoint_cache, received_setpoints)
        except Exception as e:
            logging.warning(f"Error receiving setpoints from server: {e}")
            cached_setpoints = get_setpoints_from_cache(setpoint_cache)
            if cached_setpoints:
                # ... (use cached_setpoints)
            else:
                # ... (handle empty cache, e.g., use default setpoints) """

        await asyncio.sleep(polling_interval)

    # Close the setpoint cache
    setpoint_cache.close()

async def main():
    """
    Main function to run the HVAC control loop.
    """
    # --- MQTT Setup ---
    mqtt_config = config['MQTT']
    
    # --- Create MQTT client ---
    global mqtt_client  # Make mqtt_client global to access it in other functions
    async with Client(mqtt_config['broker'], int(mqtt_config['port'])) as mqtt_client:

        polling_interval = int(config.get('HVAC', 'polling_interval'))
        await read_and_publish_sensor_data(polling_interval)

if __name__ == "__main__":
    asyncio.run(main())