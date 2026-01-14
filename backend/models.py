from sqlalchemy import Column, Integer, String, Float
from database import Base

class PatrimonioDB(Base):
    __tablename__ = "patrimonios"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_patrimonio = Column(String(100), unique=True, index=True) # O número da etiqueta
    nome = Column(String(255))
    sala = Column(String(100))
    quantidade = Column(Integer)
    valor = Column(Float) # Valor em Reais
