from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from logger_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
logger.info(f"Database connection created for {DATABASE_URL}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("SessionLocal created")
Base = declarative_base()
logger.info("Base created")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
