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
from models import Base, create_models  # Import the create_models function 

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
    with engine.connect() as connection:
        if not engine.dialect.has_schema(connection, schema_name):
            connection.execute(CreateSchema(schema_name))

    # Create the models with dynamic table names *before* creating the tables
    HvacSensorData, HvacConfig = create_models(schema_name)

    # Create the database tables within the specified schema (if they don't exist)
    Base.metadata.create_all(engine)

    # Populate hvac_config table with initial values from config.ini (if it's empty)
    Session = sessionmaker(bind=engine)
    session = Session()
    if not session.query(HvacConfig).first(): 
        for section in config.sections():
            for option in config.options(section):
                new_config = HvacConfig(section=section, option=option, value=config.get(section, option))
                session.add(new_config)
        session.commit()
    session.close()

except (OperationalError, ProgrammingError) as e:
    logging.error(f"Database error: {e}")  
    exit(1) 

# --- Relay Setup (commented out for now) ---
# ...

# --- Sensor Setup (commented out for now) ---
# ...

# --- Main Control Loop ---
try:
    while True:
        default_temperature = float(config.get('HVAC', 'default_temperature'))
        polling_interval = int(config.get('HVAC', 'polling_interval'))
        simulated_temperature = float(config.get('HVAC', 'simulated_temperature'))  # Moved this line inside the loop
        # ... (Get configuration options from config.ini)

        # 2. Read sensor data (or use simulated data for now)
        temperature_reading = simulated_temperature 
        print(f"Simulated temperature reading: {temperature_reading}°F") 

        # 3. Implement your HVAC control logic based on config options, and sensor data
        # ... (For now, you can focus on testing database interactions)

        # 4. Store sensor data in the database (example)
        Session = sessionmaker(bind=engine)
        session = Session()
        new_sensor_data = HvacSensorData(temperature=temperature_reading, timestamp=datetime.datetime.now(datetime.timezone.utc)) 
        session.add(new_sensor_data)
        session.commit()
        session.close()
        logging.info("Sensor data inserted into the database.")

        # ... (rest of the control loop)

        time.sleep(polling_interval)

except KeyboardInterrupt:
    logging.info("Keyboard interrupt detected. Exiting...")
    exit(0)