from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "sqlite:///./oaf_nursery.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
