import datetime
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

from models import Base, create_models

class DBManager:
    def __init__(self, connection_string, schema_name, sensor_mappings):
        self.connection_string = connection_string
        self.schema_name = schema_name
        self.sensor_mappings = sensor_mappings
        self.engine = None
        self.Session = None

    def initialize_db(self):
        """Initializes the database, creates the schema, and tables if they don't exist."""
        try:
            self.engine = create_engine(self.connection_string)

            # Create the schema if it doesn't exist
            with self.engine.begin() as connection:
                if not self.engine.dialect.has_schema(connection, self.schema_name):
                    connection.execute(CreateSchema(self.schema_name))

            # Create the sensor data model
            self.HvacSensorData = create_models(self.schema_name, self.sensor_mappings)

            # Create only the sensor data table
            self.HvacSensorData.__table__.create(bind=self.engine, checkfirst=True)
            logging.info("Database table for sensor data created successfully.")

            self.Session = sessionmaker(bind=self.engine)

        except (OperationalError, ProgrammingError) as e:
            logging.error(f"Database error: {e}")
            raise  # Re-raise the exception to be handled in main.py

    def insert_sensor_data(self, sensor_readings):
        """Inserts sensor data into the database."""
        session = self.Session()
        try:
            # Use an INSERT statement that should work on older SQL Server versions
            table = self.HvacSensorData.__table__
            session.execute(table.insert().values(sensor_readings))
            session.commit()
            logging.info("Simulated sensor data inserted into the database.")
        except IntegrityError as e:
            logging.error(f"Error inserting data: {e}")
            session.rollback()
        finally:
            session.close() 