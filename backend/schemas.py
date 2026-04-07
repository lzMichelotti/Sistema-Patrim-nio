from pydantic import BaseModel
from typing import Optional

#Salas 
class SalaCreate(BaseModel):
    nome: str

class SalaResponse(BaseModel):
    id: int
    nome: str

    class Config:
        from_attributes = True  #Permite ler dados do SQLAlchemy

# Patrimônios
class PatrimonioCreate(BaseModel):
    numero_patrimonio_lamic: Optional[str] = None
    numero_patrimonio_ufsm: Optional[str] = None
    nome: str
    quantidade: int = 1
    valor_total: Optional[float] = None
    sala_id: int 
    ativo: bool = True

class ComponenteCreate(BaseModel):
    nome: str
    numero_serie: Optional[str] = None
    quantidade: int = 1
    valor: Optional[float] = None
    observacao: Optional[str] = None

class ComponenteResponse(ComponenteCreate):
    id: int
    patrimonio_id: int

    class Config:
        from_attributes = True

class PatrimonioResponse(PatrimonioCreate):
    id: int
    componentes: list[ComponenteResponse] = []

    class Config:
        from_attributes = True