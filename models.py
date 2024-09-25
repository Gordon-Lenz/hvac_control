from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class HvacSensorData(Base):
    __tablename__ = 'hvac_sensor_data'
    id = Column(Integer, primary_key=True)
    sensor = Column(String(50))
    timestamp = Column(DateTime, index=True)  # Add index here
    data = Column(Float)

class HvacConfig(Base):  
    __tablename__ = 'hvac_config'
    id = Column(Integer, primary_key=True)
    section = Column(String(50))  
    option = Column(String(50))   
    value = Column(String(100))
    timestamp = Column(DateTime, index=True)  # Add index here