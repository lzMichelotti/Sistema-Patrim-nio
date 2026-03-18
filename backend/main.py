from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import graphic
import models
import schemas
from database import engine, get_db
from pdf_report import gerar_pdf_patrimonio

#Garante que o banco e as tabelas sejam criados ao iniciar a API
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Patrimônio")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


#Salas

@app.post("/salas/", response_model=schemas.SalaResponse)
def criar_sala(sala: schemas.SalaCreate, db: Session = Depends(get_db)):
    nova_sala = models.SalaDB(nome=sala.nome)
    db.add(nova_sala)
    db.commit()
    db.refresh(nova_sala)
    return nova_sala

@app.get("/salas/", response_model=list[schemas.SalaResponse])
def listar_salas(db: Session = Depends(get_db)):
    return db.query(models.SalaDB).all()

#Patrimônios

@app.post("/patrimonios/", response_model=schemas.PatrimonioResponse)
def criar_patrimonio(patrimonio: schemas.PatrimonioCreate, db: Session = Depends(get_db)):
    
    sala_existe = db.query(models.SalaDB).filter(models.SalaDB.id == patrimonio.sala_id).first()
    if not sala_existe:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    
    # Se a sala existe, criar o patrimônio
    novo_patrimonio = models.PatrimonioDB(**patrimonio.model_dump())
    db.add(novo_patrimonio)
    db.commit()
    db.refresh(novo_patrimonio)
    return novo_patrimonio

@app.get("/patrimonios/", response_model=list[schemas.PatrimonioResponse])
def listar_patrimonios(db: Session = Depends(get_db)):
    return db.query(models.PatrimonioDB).all()


#(PUT/DELETE)

@app.put("/patrimonios/{patrimonio_id}", response_model=schemas.PatrimonioResponse)
def atualizar_patrimonio(patrimonio_id: int, patrimonio: schemas.PatrimonioCreate, db: Session = Depends(get_db)):
    item_db = db.query(models.PatrimonioDB).filter(models.PatrimonioDB.id == patrimonio_id).first()
    if not item_db:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")
    
    # Sala informada para atualização realmente existe
    sala_existe = db.query(models.SalaDB).filter(models.SalaDB.id == patrimonio.sala_id).first()
    if not sala_existe:
        raise HTTPException(status_code=404, detail="A sala informada não existe")
    
    # Atualizar os dados dinamicamente
    for key, value in patrimonio.model_dump().items():
        setattr(item_db, key, value)
        
    db.commit()
    db.refresh(item_db)
    return item_db

@app.delete("/patrimonios/{patrimonio_id}")
def deletar_patrimonio(patrimonio_id: int, db: Session = Depends(get_db)):
    # Busca
    item_db = db.query(models.PatrimonioDB).filter(models.PatrimonioDB.id == patrimonio_id).first()
    if not item_db:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")
        
    db.delete(item_db)
    db.commit()
    
    return {"mensagem": f"Patrimônio ID {patrimonio_id} deletado com sucesso!"}


@app.get("/exportar_pdf")
def exportar_pdf(db: Session = Depends(get_db)):
    items = db.query(models.PatrimonioDB).all()
    buffer = gerar_pdf_patrimonio(items)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_lamic.pdf"},
    )

# ==========================================
# ROTAS DE DASHBOARD E GRÁFICOS
# ==========================================

@app.get("/graficos/valor-por-sala")
def obter_grafico_valor():
    # Chama a função criada em  graphic.py
    buffer_imagem = graphic.gerar_grafico_valor_por_sala()
    
    if not buffer_imagem:
        raise HTTPException(status_code=404, detail="Não há dados suficientes para gerar o gráfico.")
    
    # Retorna o conteúdo da memória avisando o navegador que é uma imagem PNG
    return Response(content=buffer_imagem.getvalue(), media_type="image/png")