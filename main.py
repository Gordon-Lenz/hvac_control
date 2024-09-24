import configparser
import json
import time
import datetime 
from gpiozero import OutputDevice
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError 

# --- Configuration ---
config = configparser.ConfigParser()
config.read('config.ini')

# Load relay and sensor mappings from JSON (commented out for now)
# with open('pin_mappings.json', 'r') as f:
#    mappings = json.load(f)

# relay_mappings = mappings['relays']
# sensor_mappings = mappings['sensors']

# Get the HVAC unit ID from the config file
hvac_unit_id = config.get('HVAC', 'hvac_unit_id')

# Define the schema name based on the unit ID
schema_name = f'hvac_{hvac_unit_id}'

# --- Database Setup ---
db_config = config['DATABASE']

# Construct the connection string 
connection_string = f'mssql+pyodbc://hvac_admin:p@localhost\\SQLEXPRESS/{db_config["database"]}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'

try:
    engine = create_engine(connection_string)

    # Create the schema if it doesn't exist
    with engine.connect() as connection:
        if not engine.dialect.has_schema(connection, schema_name):
            connection.execute(CreateSchema(schema_name))

    Base = declarative_base()

    class HvacSensorData(Base):
        __tablename__ = 'hvac_sensor_data'
        __table_args__ = {'schema': schema_name}
        id = Column(Integer, primary_key=True)
        sensor = Column(String(50))
        timestamp = Column(DateTime)
        data = Column(Float) 

    class HvacConfig(Base):  
        __tablename__ = 'hvac_config'
        __table_args__ = {'schema': schema_name}
        id = Column(Integer, primary_key=True)
        config_field = Column(String(50))
        value = Column(String(100))
        timestamp = Column(DateTime)

    # Create the database tables within the specified schema (if they don't exist)
    Base.metadata.create_all(engine)

except OperationalError as e:
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

        # 3. Implement your HVAC control logic based on config options, and sensor data
        # ... (For now, you can focus on testing database interactions)

        # 4. Store sensor data in the database (example)
        Session = sessionmaker(bind=engine)
        session = Session()
        new_sensor_data = HvacSensorData(sensor='temperature', timestamp=datetime.datetime.now(), data=temperature_reading)
        session.add(new_sensor_data)
        session.commit()
        session.close()

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