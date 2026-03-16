import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./patrimonio.db")


def _is_windows_absolute_path(path_value: str) -> bool:
    return len(path_value) > 2 and path_value[1] == ":" and path_value[2] in ("/", "\\")


def _normalize_sqlite_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    raw_path = database_url[len("sqlite:///") :]
    if raw_path in ("", ":memory:"):
        return database_url

    if os.path.isabs(raw_path) or _is_windows_absolute_path(raw_path):
        db_path = Path(raw_path)
    else:
        base_dir = Path(__file__).resolve().parent
        db_path = (base_dir / raw_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


DATABASE_URL = _normalize_sqlite_url(DATABASE_URL)

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Essa função auxilia na hora de injetar o banco de dados nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()