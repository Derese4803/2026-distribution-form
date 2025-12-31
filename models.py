from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'oaf_back_checks'
    id = Column(Integer, primary_key=True)
    
    # Location and Identifiers
    woreda = Column(String)
    kebele = Column(String)
    checker_fa_name = Column(String)
    checker_cbe_name = Column(String) 
    checker_phone = Column(String)    
    fenced = Column(String)           

    # Guava Group
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)
    total_guava_sockets = Column(Integer) # Calculated

    # Gesho Group
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)
    total_gesho_sockets = Column(Integer) # Calculated

    # Lemon Group
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)
    # Total Lemon Removed

    # Grevillea Group
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer)
    total_grevillea_sockets = Column(Integer) # Calculated
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
