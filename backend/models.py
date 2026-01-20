"""Modelos dinâmicos por sala.

Cada sala ganha uma tabela própria com as colunas solicitadas.
"""

from sqlalchemy import Column, Integer, String, Float
import unicodedata

from database import Base
from salas import SALAS


def _slugify_sala(nome: str) -> str:
    """Gera um slug ASCII seguro para usar no nome da tabela."""
    normalized = unicodedata.normalize("NFKD", nome)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in ascii_only)
    collapsed = "_".join(part for part in cleaned.split("_") if part)
    return collapsed.lower()


def _build_model_class(sala: str):
    slug = _slugify_sala(sala)
    class_name = "Patrimonio" + "".join(word.capitalize() for word in slug.split("_")) + "DB"
    table_name = f"patrimonios_{slug}"

    attrs = {
        "__tablename__": table_name,
        "id": Column(Integer, primary_key=True, index=True),
        "numero_patrimonio_lamic": Column(String(100), index=True),
        "numero_patrimonio_ufsm": Column(String(100), nullable=True),
        "nome": Column(String(255)),
        "sala": Column(String(100), default=sala),
        "quantidade": Column(Integer),
        "valor_total": Column(Float),
    }

    return type(class_name, (Base,), attrs)


# Dicionário sala -> classe do modelo
SALA_MODELS = {sala: _build_model_class(sala) for sala in SALAS}


def get_model_for_sala(sala: str):
    """Retorna a classe do modelo correspondente à sala informada."""
    if sala not in SALA_MODELS:
        raise ValueError(f"Sala desconhecida: {sala}")
    return SALA_MODELS[sala]


__all__ = ["SALA_MODELS", "get_model_for_sala"]
