# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Initialisation de Base
# ``__allow_unmapped__`` est activé pour éviter les erreurs d'annotations
# non typées avec SQLAlchemy 2 lors des tests. Les modèles existants utilisent
# encore la syntaxe déclarative classique sans les génériques ``Mapped[]`` ;
# cette option permet de conserver ces modèles tels quels pour l'instant.
Base = declarative_base()
Base.__allow_unmapped__ = True

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
