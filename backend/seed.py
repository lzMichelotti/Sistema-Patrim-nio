import models
from database import SessionLocal, engine

# Garante que as tabelas existam antes de tentar inserir os dados
models.Base.metadata.create_all(bind=engine)

SALAS_FIXAS = [
    "DESCONTAMINAÇÃO", "PREPARAÇÃO", "EXTRAÇÃO", "REFRIGERAÇÃO",
    "CROMATOGRAFIA", "CROMATOGRAFIA HP1", "CROMATOGRAFIA HP2", "CROMATOGRAFIA HP3",
    "CROMATOGRAFIA HP4", "CROMATOGRAFIA HP5", "CROMATOGRAFIA HP6", "CROMATOGRAFIA HP7",
    "CROMATOGRAFIA GC", "SALA CARLOS", "COORDENAÇÃO", "NIRS",
    "SALA ASSESSORIA CIENTÍFICA", "RECEPÇÃO", "SALA DIMA",
    "SALA BOLSISTAS", "SALA FREEZER", "ALMOXARIFADO DO 3° ANDAR",
    "SALA 5005 SUBSOLO", "SALA 5137", "SALA REUNIÕES", "SALA CAFÉ",
    "BANHEIRO ENTRADA", "BANHEIRO FUNDOS", "EQUIPAMENTO EXTERNO"
]

def popular_salas():
    db = SessionLocal()
    try:
        print("Iniciando a verificação e cadastro das salas...")
        for nome_sala in SALAS_FIXAS:
            # Verifica se a sala já existe para não criar duplicatas se você rodar o script duas vezes
            sala_existente = db.query(models.SalaDB).filter(models.SalaDB.nome == nome_sala).first()
            
            if not sala_existente:
                nova_sala = models.SalaDB(nome=nome_sala)
                db.add(nova_sala)
                print(f"✅ Sala '{nome_sala}' adicionada.")
            else:
                print(f"➡️ Sala '{nome_sala}' já estava cadastrada.")
        
        db.commit()
        print("Finalizado! Todas as salas estão no banco de dados.")
    finally:
        db.close()

if __name__ == "__main__":
    popular_salas()