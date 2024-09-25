import datetime  

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class HvacSensorData(Base):
    __tablename__ = 'hvac_sensor_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now(datetime.timezone.utc))  # Updated default value
    temperature = Column(Float, nullable=True) 
    humidity = Column(Float, nullable=True)
    current_phase1 = Column(Float, nullable=True)
    current_phase2 = Column(Float, nullable=True)
    current_phase3 = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)

class HvacConfig(Base):  
    __tablename__ = 'hvac_config'
    id = Column(Integer, primary_key=True)
    section = Column(String(50))  
    option = Column(String(50))   
    value = Column(String(100))
    timestamp = Column(DateTime, index=True, default=datetime.datetime.now(datetime.timezone.utc))  # Updated default value