from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class SalaDB(Base):
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, index=True, nullable=False)
    
    # Isso diz ao SQLAlchemy: "Uma sala possui vários patrimônios"
    patrimonios = relationship("PatrimonioDB", back_populates="sala")


class PatrimonioDB(Base):
    __tablename__ = "patrimonios"

    id = Column(Integer, primary_key=True, index=True)
    
    # Aqui substituímos o nome da sala pelo ID dela na outra tabela
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=False)
    
    # Os dados específicos do ativo que você listou
    numero_patrimonio_lamic = Column(String(100), unique=True, index=True, nullable=True)
    numero_patrimonio_ufsm = Column(String(100), nullable=True)
    nome = Column(String(255), nullable=False)
    quantidade = Column(Integer, default=1)
    valor_total = Column(Float, nullable=True)
    ativo = Column(Boolean, default=True)
    
    # Isso diz ao SQLAlchemy: "Este patrimônio pertence a uma sala"
    sala = relationship("SalaDB", back_populates="patrimonios")
    componentes = relationship("ComponenteDB", back_populates="patrimonio", cascade="all, delete-orphan")


class ComponenteDB(Base):
    __tablename__ = "componentes"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    numero_serie = Column(String(100), nullable=True)
    quantidade = Column(Integer, default=1)
    valor = Column(Float, nullable=True)
    observacao = Column(String(500), nullable=True)

    patrimonio = relationship("PatrimonioDB", back_populates="componentes")