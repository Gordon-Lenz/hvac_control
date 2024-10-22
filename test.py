from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
import configparser 

# --- Configuration ---
config = configparser.ConfigParser()
config.read('config.ini')

# --- Database Setup with Error Handling ---
db_config = config['DATABASE']

# Construct the connection string
connection_string = f'mssql+pyodbc://{db_config["username"]}:{db_config["password"]}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}&trusted_connection=yes'

engine = create_engine(connection_string)

schema_name = "hvac_4test"

with engine.begin() as connection:  # Use engine.begin() to manage the transaction
    if not engine.dialect.has_schema(connection, schema_name):
        connection.execute(CreateSchema(schema_name))