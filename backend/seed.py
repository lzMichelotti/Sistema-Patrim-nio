import argparse

import models
from database import SessionLocal, engine

# Garante que as tabelas existam antes de tentar inserir os dados.
models.Base.metadata.create_all(bind=engine)

SALAS_FIXAS = [
    "DESCONTAMINAÇÃO", "PREPARAÇÃO", "EXTRAÇÃO", "REFRIGERAÇÃO",
    "CROMATOGRAFIA", "CROMATOGRAFIA HP1", "CROMATOGRAFIA HP2", "CROMATOGRAFIA HP3",
    "CROMATOGRAFIA HP4", "CROMATOGRAFIA HP5", "CROMATOGRAFIA HP6", "CROMATOGRAFIA HP7",
    "CROMATOGRAFIA GC", "SALA CARLOS", "COORDENAÇÃO", "NIRS",
    "SALA ASSESSORIA CIENTÍFICA", "RECEPÇÃO", "SALA DIMA",
    "SALA BOLSISTAS", "SALA FREEZER", "ALMOXARIFADO DO 3° ANDAR",
    "SALA 5005 SUBSOLO", "SALA 5137", "SALA REUNIÕES", "SALA CAFÉ",
    "BANHEIRO ENTRADA", "BANHEIRO FUNDOS", "EQUIPAMENTO EXTERNO",
]

ITENS_PADRAO = [
    {"nome": "Computador", "quantidade": 1, "valor_total": 4500.0},
    {"nome": "Mesa de trabalho", "quantidade": 1, "valor_total": 850.0},
    {"nome": "Cadeira ergonômica", "quantidade": 2, "valor_total": 1200.0},
    {"nome": "Armário de armazenamento", "quantidade": 1, "valor_total": 1800.0},
]


def popular_salas(db):
    salas = []
    total_novas = 0

    print("Iniciando a verificação e cadastro das salas...")
    for nome_sala in SALAS_FIXAS:
        sala_existente = db.query(models.SalaDB).filter(models.SalaDB.nome == nome_sala).first()

        if not sala_existente:
            sala_existente = models.SalaDB(nome=nome_sala)
            db.add(sala_existente)
            db.flush()
            total_novas += 1
            print(f"Sala '{nome_sala}' adicionada.")
        else:
            print(f"Sala '{nome_sala}' já estava cadastrada.")

        salas.append(sala_existente)

    return salas, total_novas


def _gerar_numero_patrimonio_lamic(db, sala_id, indice_item):
    tentativa = 0
    while True:
        sufixo = f"-{tentativa}" if tentativa else ""
        codigo = f"LAMIC-{sala_id:03d}-{indice_item:02d}{sufixo}"
        existe = (
            db.query(models.PatrimonioDB.id)
            .filter(models.PatrimonioDB.numero_patrimonio_lamic == codigo)
            .first()
        )
        if not existe:
            return codigo
        tentativa += 1


def popular_itens_padrao(db, salas):
    total_novos_itens = 0
    print("Iniciando a verificação e cadastro dos patrimônios por sala...")

    for sala in salas:
        for indice_item, item in enumerate(ITENS_PADRAO, start=1):
            item_existente = (
                db.query(models.PatrimonioDB)
                .filter(
                    models.PatrimonioDB.sala_id == sala.id,
                    models.PatrimonioDB.nome == item["nome"],
                )
                .first()
            )

            if item_existente:
                continue

            numero_lamic = _gerar_numero_patrimonio_lamic(db, sala.id, indice_item)
            numero_ufsm = f"UFSM-{sala.id:03d}-{indice_item:02d}"

            novo_item = models.PatrimonioDB(
                sala_id=sala.id,
                numero_patrimonio_lamic=numero_lamic,
                numero_patrimonio_ufsm=numero_ufsm,
                nome=item["nome"],
                quantidade=item["quantidade"],
                valor_total=item["valor_total"],
            )
            db.add(novo_item)
            total_novos_itens += 1

        print(f"Sala '{sala.nome}' verificada.")

    return total_novos_itens


def popular_banco(com_itens=False):
    db = SessionLocal()
    try:
        salas, total_novas_salas = popular_salas(db)
        total_novos_itens = 0

        if com_itens:
            total_novos_itens = popular_itens_padrao(db, salas)

        db.commit()
        print(
            "Finalizado! "
            f"Salas verificadas: {len(salas)} | "
            f"Novas salas: {total_novas_salas} | "
            f"Novos itens: {total_novos_itens}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _parse_args():
    parser = argparse.ArgumentParser(description="Popula o banco com salas e, opcionalmente, itens padrão.")
    parser.add_argument(
        "--com-itens",
        action="store_true",
        help="Também cadastra itens padrão em todas as salas.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    popular_banco(com_itens=args.com_itens)
