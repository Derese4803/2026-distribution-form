from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Woreda(Base):
    __tablename__ = 'woredas'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    kebeles = relationship("Kebele", backref="woreda", cascade="all, delete-orphan")

class Kebele(Base):
    __tablename__ = 'kebeles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    woreda_id = Column(Integer, ForeignKey('woredas.id'))

class Farmer(Base):
    __tablename__ = 'farmers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    woreda = Column(String)
    kebele = Column(String)
    officer_name = Column(String)
    audio_url = Column(String)
    # Seedlings
    gesho = Column(Integer, default=0)
    giravila = Column(Integer, default=0)
    diceres = Column(Integer, default=0)
    wanza = Column(Integer, default=0)
    papaya = Column(Integer, default=0)
    moringa = Column(Integer, default=0)
    lemon = Column(Integer, default=0)
    arzelibanos = Column(Integer, default=0)
    guava = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class BackCheck(Base):
    __tablename__ = 'back_checks'
    id = Column(Integer, primary_key=True)
    checker_name = Column(String)
    woreda = Column(String)
    kebele = Column(String)
    fenced = Column(String)
    # Guava
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)
    # Lemon
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)
    total_lemon_sockets = Column(Integer) # Automatic Calculation field
    # Gesho
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)
    # Grevillea
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
