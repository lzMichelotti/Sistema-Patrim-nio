from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do banco de dados
DATABASE_URL = "sqlite:///./patrimonio.db"

# Criação da engine de conexão
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

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
