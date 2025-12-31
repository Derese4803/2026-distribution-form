from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import sessionmaker

# This creates a local file named 'oaf_nursery.db'
# 'check_same_thread' is required for SQLite to work with Streamlit
DATABASE_URL = "sqlite:///./oaf_nursery.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
