from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'oaf_back_checks'
    id = Column(Integer, primary_key=True)
    
    # Location and Identifiers
    woreda = Column(String)
    cluster = Column(String)
    kebele = Column(String)
    tno_name = Column(String)
    checker_fa_name = Column(String)
    checker_cbe_name = Column(String) 
    checker_phone = Column(String)    
    fenced = Column(String)           

    # Guava Group
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)
    total_guava_sockets = Column(Integer)

    # Gesho Group
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)
    total_gesho_sockets = Column(Integer)

    # Lemon Group
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)
    # Note: No total_lemon_sockets as per your request

    # Grevillea Group
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer)
    total_grevillea_sockets = Column(Integer) 
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
