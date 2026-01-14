from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Pega a URL do .env. Se não existir, usa SQLite como fallback (segurança)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./patrimonio.db")

# Configuração específica para SQLite vs Outros Bancos
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Criação da engine de conexão
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Sessão do banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos herdarem
Base = declarative_base()

# Dependência para injetar o banco nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()