from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'back_checks'
    id = Column(Integer, primary_key=True)
    
    # Location and Identifiers
    woreda = Column(String)
    kebele = Column(String)
    checker_fa_name = Column(String)  # Name of Back checker (FAs)
    checker_cbe_name = Column(String) # Back checker (CBE)
    checker_phone = Column(String)    # Back checker phone #
    fenced = Column(String)           # Nursery Fenced (Yes/No)
    
    # Guava Metrics (Expect 13)
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)
    
    # Lemon Metrics (Expect 13)
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)
    total_lemon_sockets = Column(Integer) # Auto-calculated
    
    # Gesho Metrics (Expect 16)
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)
    
    # Grevillea Metrics (Expect 16)
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer)
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
