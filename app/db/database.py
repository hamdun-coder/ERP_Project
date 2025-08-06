# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Initialisation de Base
Base = declarative_base()
Base.__allow_unmapped__ = True  # SQLAlchemy 2.x compat: allow legacy type hints

# Production engine par défaut
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)

# Session liée à l’engine de prod (surchargée en test)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dépendance utilisée par FastAPI (surchargée dans les tests)
from sqlalchemy.orm import Session
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
