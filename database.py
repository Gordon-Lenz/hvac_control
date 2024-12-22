# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy.exc import OperationalError, ProgrammingError

Base = declarative_base()

def create_database_engine(connection_string, schema_name):
    """
    Creates a SQLAlchemy engine and ensures the schema exists.
    """
    try:
        engine = create_engine(connection_string)

        with engine.begin() as connection:
            if not engine.dialect.has_schema(connection, schema_name):
                connection.execute(CreateSchema(schema_name))

        return engine
    
    except OperationalError as e:
        print(f"Error connecting to the database or creating schema: {e}")
        exit(1) 

def create_database_session(engine):
    """
    Creates a SQLAlchemy session factory.
    """
    return sessionmaker(bind=engine)