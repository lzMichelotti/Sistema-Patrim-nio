from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import google.genai as genai
import json
import os
from dotenv import load_dotenv
import uuid 
import traceback 

# Importações dos módulos refatorados
from database import engine, get_db, Base
from models import PatrimonioDB

load_dotenv()

# --- Inicialização do Banco de Dados ---
# Cria as tabelas no banco automaticamente se não existirem
Base.metadata.create_all(bind=engine)

# --- Schemas (Pydantic) ---
# Classes para validação de dados que entram e saem da API
class PatrimonioCreate(BaseModel):
    numero_patrimonio: str
    nome: str
    sala: str
    quantidade: int
    valor: float

class PatrimonioResponse(PatrimonioCreate):
    id: int
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    message: str

# --- Configuração da API ---
app = FastAPI()

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rotas da API ---

@app.post("/patrimonios/", response_model=PatrimonioResponse)
def criar_patrimonio(item: PatrimonioCreate, db: Session = Depends(get_db)):
    db_item = PatrimonioDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/patrimonios/", response_model=list[PatrimonioResponse])
def listar_patrimonios(db: Session = Depends(get_db)):
    return db.query(PatrimonioDB).all()

@app.put("/patrimonios/{id}", response_model=PatrimonioResponse)
def atualizar_patrimonio(id: int, item: PatrimonioCreate, db: Session = Depends(get_db)):
    db_item = db.query(PatrimonioDB).filter(PatrimonioDB.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/patrimonios/{id}")
def deletar_patrimonio(id: int, db: Session = Depends(get_db)):
    item = db.query(PatrimonioDB).filter(PatrimonioDB.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    db.delete(item)
    db.commit()
    return {"mensagem": "Item deletado com sucesso"}

# --- Rotas de Relatórios ---

@app.get("/exportar_excel")
def exportar_excel(db: Session = Depends(get_db)):
    items = db.query(PatrimonioDB).all()
    
    dados = []
    for item in items:
        dados.append({
            "Patrimônio": item.numero_patrimonio,
            "Nome/Descrição": item.nome,
            "Sala": item.sala,
            "Quantidade": item.quantidade,
            "Valor (R$)": item.valor
        })
    
    df = pd.DataFrame(dados)
    stream = io.BytesIO()
    df.to_excel(stream, index=False, engine='openpyxl')
    stream.seek(0)
    
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventario_lamic.xlsx"}
    )

@app.get("/exportar_pdf")
def exportar_pdf(db: Session = Depends(get_db)):
    items = db.query(PatrimonioDB).all()
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Relatório de Patrimônio - LAMIC", styles['Title']))
    
    data = [['Patrimônio', 'Nome', 'Sala', 'Qtd', 'Valor']]
    
    for item in items:
        data.append([
            item.numero_patrimonio,
            item.nome[:30],
            item.sala,
            str(item.quantidade),
            f"R$ {item.valor}"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_lamic.pdf"}
    )

# --- Integração com Gemini AI ---

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@app.post("/chat")
def chat_with_ai(dados: ChatMessage, db: Session = Depends(get_db)):
    print(f"--- [DEBUG] INICIANDO CHAT --- Mensagem recebida: {dados.message}")
    message_lower = dados.message.lower()
    
    # Detecção de intenção de cadastro
    if any(keyword in message_lower for keyword in [
        "preencher", "adicionar", "cadastrar", "registrar", 
        "registre", "cria", "insira", "novo", "lançar"
    ]):
        print("--- [DEBUG] INTENÇÃO DE CADASTRO DETECTADA ---")
        
        prompt = f"""
        Você é um assistente de cadastro de patrimônio.
        Analise o texto abaixo e extraia os dados para formato JSON.
        Texto: "{dados.message}"
        
        Regras:
        - Retorne APENAS o JSON válido.
        - Campos obrigatórios: nome (string), sala (string), quantidade (int), valor (float).
        - Campo opcional: numero_patrimonio (string). Se o usuário disser (ex: "código X", "patrimônio Y"), extraia. Se não, deixe null.
        - O valor deve ser numérico (ex: 1200.50), sem R$.
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
            dados_json = json.loads(texto_limpo)
            
            if not dados_json.get("numero_patrimonio"):
                dados_json["numero_patrimonio"] = f"AUTO-{str(uuid.uuid4())[:6].upper()}"

            item_para_salvar = PatrimonioCreate(**dados_json)
            
            # Reutiliza a lógica de criação chamando a função da rota ou inserindo direto
            # Vamos inserir direto para evitar problemas de dependência circular ou duplicação de lógica
            db_item = PatrimonioDB(**item_para_salvar.dict())
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            
            print(f"--- [DEBUG] SUCESSO! ID GERADO: {db_item.id} ---")
            
            return {
                "type": "success", 
                "message": f"Certo! Item '{db_item.nome}' ({db_item.numero_patrimonio}) registrado.",
                "data": {
                    "id": db_item.id,
                    "numero_patrimonio": db_item.numero_patrimonio,
                    "nome": db_item.nome,
                    "sala": db_item.sala,
                    "quantidade": db_item.quantidade,
                    "valor": db_item.valor
                }
            }

        except json.JSONDecodeError:
            return {"type": "chat", "message": "Entendi que você quer cadastrar, mas não consegui entender os dados. Tente reformular."}
        
        except Exception as e:
            traceback.print_exc()
            return {"type": "error", "message": f"Erro interno ao salvar: {str(e)}"}

    else:
        # Chat Conversacional
        prompt = f"""
        Você é um assistente útil para o sistema de gestão de patrimônio da LAMIC.
        Responda de forma amigável e útil à seguinte mensagem do usuário: "{dados.message}"
        Mantenha a resposta concisa.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return {"type": "chat", "message": response.text.strip()}
