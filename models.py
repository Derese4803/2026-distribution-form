from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'oaf_back_checks'
    
    # --- 1. ID & Metadata ---
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # --- 2. Location & Personnel / ቦታ እና ሰራተኛ ---
    woreda = Column(String)
    cluster = Column(String)
    kebele = Column(String)
    tno_name = Column(String)
    checker_fa_name = Column(String)
    cbe_acc = Column(String)          # CBE Account Number
    checker_phone = Column(String)    
    fenced = Column(String)           # Yes/No

    # --- 3. Guava (ዘይቶን) ---
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)   # Expected 13
    total_guava_sockets = Column(Integer)
    
    # --- 4. Gesho (ጌሾ) ---
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)   # Expected 16
    total_gesho_sockets = Column(Integer)

    # --- 5. Lemon (ሎሚ) ---
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)   # Expected 13
    total_lemon_sockets = Column(Integer)

    # --- 6. Grevillea (ግራቪሊያ) ---
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer) # Expected 16
    total_grevillea_sockets = Column(Integer) 
    
    # --- 7. Remarks & Photos / ማስታወሻ እና ፎቶ ---
    auto_remark = Column(String)      # Stores "Over/Under/Correct"
    general_remark = Column(String)   # Manual notes from back-checker
    photo = Column(Text)              # Stores photo as Base64 string
