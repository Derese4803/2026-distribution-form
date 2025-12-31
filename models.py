from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'oaf_back_checks'
    id = Column(Integer, primary_key=True)
    
    # Personnel & Location
    woreda = Column(String)
    cluster = Column(String)
    kebele = Column(String)
    tno_name = Column(String)
    checker_fa_name = Column(String)
    cbe_acc = Column(String)
    checker_phone = Column(String)    
    fenced = Column(String)           

    # Species Data
    guava_beds = Column(Integer); guava_length = Column(Float); guava_sockets = Column(Integer); total_guava_sockets = Column(Integer)
    gesho_beds = Column(Integer); gesho_length = Column(Float); gesho_sockets = Column(Integer); total_gesho_sockets = Column(Integer)
    lemon_beds = Column(Integer); lemon_length = Column(Float); lemon_sockets = Column(Integer); total_lemon_sockets = Column(Integer)
    grevillea_beds = Column(Integer); grevillea_length = Column(Float); grevillea_sockets = Column(Integer); total_grevillea_sockets = Column(Integer) 
    
    # Remarks / አስተያየቶች
    auto_remark = Column(String)    # Automatic Over/Under status
    general_remark = Column(String) # Manual user comments
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
