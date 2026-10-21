import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Endereço do PostgreSQL. Em produção vem do .env (ZELUS_DATABASE_URL); sem ele, usa o banco local de desenvolvimento.
SQLALCHEMY_DATABASE_URL = os.getenv("ZELUS_DATABASE_URL", "postgresql://postgres:root@localhost:5432/zelus")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
