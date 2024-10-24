import configparser
import json
import time
import datetime
import logging
from gpiozero import OutputDevice
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

# Import the models from your new file
from models import Base, create_models  

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

# Load relay and sensor mappings from JSON
with open('pin_mappings.json', 'r') as f:
   mappings = json.load(f)

# Get the HVAC unit ID from the config file
hvac_unit_id = config.get('HVAC', 'hvac_unit_id')

# Define the schema name based on the unit ID
schema_name = f'hvac_{hvac_unit_id}'

# --- Database Setup with Error Handling ---
db_config = config['DATABASE']

# Construct the connection string
connection_string = f'mssql+pyodbc://{db_config["username"]}:{db_config["password"]}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}&trusted_connection=yes'

try:
    engine = create_engine(connection_string)

    # Create the schema if it doesn't exist
    with engine.begin() as connection:
        if not engine.dialect.has_schema(connection, schema_name):
            connection.execute(CreateSchema(schema_name))

    # Create the models with dynamic table names and columns
    HvacSensorData, HvacConfig = create_models(schema_name, mappings['sensors'])  # Pass sensor mappings

    # Create the database tables within the specified schema (if they don't exist)
    Base.metadata.create_all(engine)
    logging.info("Database tables created successfully.")

except (OperationalError, ProgrammingError) as e:
    logging.error(f"Database error: {e}")  
    exit(1) 

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

# --- Main Control Loop ---
try:
    while True:
        # Get other configuration options from the config.ini file
        default_temperature = float(config.get('HVAC', 'default_temperature'))
        polling_interval = int(config.get('GLOBAL', 'polling_interval'))
        simulated_temperature = float(config.get('HVAC', 'simulated_temperature')) 

        # 2. Read sensor data (or use simulated data for now)
        temperature_reading = simulated_temperature 
        print(f"Simulated temperature reading: {temperature_reading}°F") 

        # 3. Implement your HVAC control logic based on config options, and sensor data
        # ... (For now, you can focus on testing database interactions)

        # 4. Store sensor data in the database (example)
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
                        db_config_option.timestamp = datetime.datetime.now(datetime.timezone.utc)  # Update timestamp in database
                        logging.info(f"Updated '{option}' in section '{section}' from database.")
                else:
                    # Option doesn't exist in the database, add it
                    new_config = HvacConfig(section=section, option=option, value=config.get(section, option))
                    session.add(new_config)
                    logging.info(f"Added '{option}' in section '{section}' to database.")

        # Write the updated config back to config.ini
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        session.commit()
        session.close()

        new_sensor_data = HvacSensorData(temperature_inlet=temperature_reading, timestamp=datetime.datetime.now(datetime.timezone.utc)) 
        session.add(new_sensor_data)
        session.commit()
        session.close()
        logging.info("Sensor data inserted into the database.")

        # Basic Example: Turn on HVAC if temperature is below set point (commented out for now)
        # if simulated_temperature < default_temperature: 
        #     relays['HVAC_POWER'].on()
        #     # ... (Set mode and fan speed based on your logic)
        # else:
        #     relays['HVAC_POWER'].off()

        time.sleep(polling_interval) 

except KeyboardInterrupt:
    # Cleanup on exit (commented out for now, since relays are not being used)
    # for relay in relays.values():
    #     relay.off()
    print("Exiting...")