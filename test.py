import configparser


config = configparser.ConfigParser()
config.read('config.ini')

# --- Database Setup ---
db_config = config['DATABASE']

connection_string_correcyt = f'mssql+pyodbc://hvac_admin:p@localhost\\SQLEXPRESS/{db_config["database"]}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'

# Construct the connection string with optional debug settings
connection_string = f'mssql+pyodbc://{db_config["username"]}:{db_config["password"]}@{db_config["server"]}/{db_config["database"]}?driver={db_config["driver"]}'
print(connection_string_correcyt)
print(connection_string)
