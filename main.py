import configparser
import json
import time
import datetime 
from gpiozero import OutputDevice
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError 

# Import the models from your new file
from models import Base, HvacSensorData, HvacConfig 

# --- Configuration ---
config = configparser.ConfigParser()
config.read('config.ini')

# Get the HVAC unit ID from the config file
hvac_unit_id = config.get('HVAC', 'hvac_unit_id')

# Define the schema name based on the unit ID
schema_name = f'hvac_{hvac_unit_id}'

# --- Database Setup ---
db_config = config['DATABASE']

# Construct the connection string
connection_string = f'mssql+pyodbc://{db_config["username"]}:{db_config["password"]}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}&trusted_connection=yes'

try:
    engine = create_engine(connection_string)

    # Create the schema if it doesn't exist
    with engine.connect() as connection:
        if not engine.dialect.has_schema(connection, schema_name):
            connection.execute(CreateSchema(schema_name))

    # Add schema to table arguments after importing
    HvacSensorData.__table_args__ = {'schema': schema_name}
    HvacConfig.__table_args__ = {'schema': schema_name}

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
    print(f"Error connecting to the database or creating schema: {e}")
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
        polling_interval = int(config.get('HVAC', 'polling_interval'))
        simulated_temperature = float(config.get('HVAC', 'simulated_temperature')) 

        # 2. Read sensor data (or use simulated data for now)
        temperature_reading = simulated_temperature 
        print(f"Simulated temperature reading: {temperature_reading}°F")

        # 3. Implement your HVAC control logic based on config options and sensor data
        # ... (For now, you can focus on testing database interactions)

        # 4. Store sensor data in the database
        Session = sessionmaker(bind=engine)
        session = Session()
        new_sensor_data = HvacSensorData(sensor='temperature', timestamp=datetime.datetime.now(), data=temperature_reading)
        session.add(new_sensor_data)
        session.commit()
        session.close()
        print("Sensor data inserted into the database.")

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