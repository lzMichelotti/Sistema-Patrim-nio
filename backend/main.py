# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

load_dotenv()

# --- 1. Configuração do Banco de Dados (SQLite por enquanto) ---
DATABASE_URL = "sqlite:///./patrimonio.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Criação da Tabela (Model) ---
class PatrimonioDB(Base):
    __tablename__ = "patrimonios"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_patrimonio = Column(String, unique=True, index=True) # O número da etiqueta
    nome = Column(String)
    sala = Column(String)
    quantidade = Column(Integer)
    valor = Column(Float) # Valor em Reais

# Cria as tabelas no banco automaticamente
Base.metadata.create_all(bind=engine)

# --- 3. Validação de Dados (Schema - Pydantic) ---
# Isso garante que o React mande os dados certos
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

# --- 4. A Aplicação (API) ---
app = FastAPI()

# Liberar o acesso para o React conversar com o Python
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Quem pode acessar?
    allow_credentials=True,
    allow_methods=["*"],         # Quais métodos? (GET, POST, etc)
    allow_headers=["*"],
)

# Dependência para pegar o banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota para CRIAR um patrimônio
@app.post("/patrimonios/", response_model=PatrimonioResponse)
def criar_patrimonio(item: PatrimonioCreate, db: Session = Depends(get_db)):
    db_item = PatrimonioDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Rota para LISTAR tudo
@app.get("/patrimonios/", response_model=list[PatrimonioResponse])
def listar_patrimonios(db: Session = Depends(get_db)):
    return db.query(PatrimonioDB).all()

#Rota para DELETAR um patrimônio pelo ID
@app.delete("/patrimonios/{id}")
def deletar_patrimonio(id: int, db: Session = Depends(get_db)):
    # Busca o item pelo ID
    item = db.query(PatrimonioDB).filter(PatrimonioDB.id == id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Deleta e salva
    db.delete(item)
    db.commit()
    return {"mensagem": "Item deletado com sucesso"}

@app.get("/exportar_excel")
def exportar_excel(db: Session = Depends(get_db)):
    # 1. Busca tudo no banco
    items = db.query(PatrimonioDB).all()
    
    # 2. Transforma em uma lista de dicionários (para o Pandas entender)
    # Aqui a gente escolhe quais colunas vão para o Excel e muda o nome delas para ficar bonito
    dados = []
    for item in items:
        dados.append({
            "Patrimônio": item.numero_patrimonio,
            "Nome/Descrição": item.nome,
            "Sala": item.sala,
            "Quantidade": item.quantidade,
            "Valor (R$)": item.valor
        })
    
    # 3. Cria o DataFrame (a tabela do Excel na memória)
    df = pd.DataFrame(dados)
    
    # 4. Escreve o arquivo na memória RAM (buffer)
    stream = io.BytesIO()
    # index=False remove aquela coluna 0,1,2,3 que o pandas cria
    df.to_excel(stream, index=False, engine='openpyxl')
    stream.seek(0) # Volta o ponteiro para o início do arquivo
    
    # 5. Retorna o arquivo para o navegador baixar
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventario_lamic.xlsx"}
    )

@app.get("/exportar_pdf")
def exportar_pdf(db: Session = Depends(get_db)):
    # 1. Busca os dados
    items = db.query(PatrimonioDB).all()
    
    # 2. Prepara o Buffer na memória (igual ao Excel)
    buffer = io.BytesIO()
    
    # 3. Cria o documento A4
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Adiciona um Título
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Relatório de Patrimônio - LAMIC", styles['Title']))
    
    # 4. Monta os dados da Tabela (Lista de Listas)
    # Primeira linha é o Cabeçalho
    data = [['Patrimônio', 'Nome', 'Sala', 'Qtd', 'Valor']]
    
    # Adiciona as linhas do banco
    for item in items:
        data.append([
            item.numero_patrimonio,
            item.nome[:30], # Corta o nome se for muito grande para caber
            item.sala,
            str(item.quantidade),
            f"R$ {item.valor}"
        ])
    
    # 5. Configura o visual da Tabela
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Fundo cinza no cabeçalho
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Texto branco no cabeçalho
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # Centraliza tudo
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Fonte negrito no cabeçalho
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black) # Grades pretas em volta de tudo
    ]))
    
    elements.append(table)
    
    # 6. Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_lamic.pdf"}
    )

# Configuração da API do Gemini
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class ChatMessage(BaseModel):
    message: str



@app.post("/chat")
def chat_with_ai(dados: ChatMessage, db: Session = Depends(get_db)):
    # LOG 1: Avisa que a requisição chegou
    print(f"--- [DEBUG] INICIANDO CHAT --- Mensagem recebida: {dados.message}")
    
    message_lower = dados.message.lower()
    
    # Verifica se é uma solicitação de preenchimento
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
            print("--- [DEBUG] ENVIANDO PROMPT PARA O GEMINI ---")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
            print(f"--- [DEBUG] RESPOSTA DA IA (TEXTO): {texto_limpo}")
            
            dados_json = json.loads(texto_limpo)
            print(f"--- [DEBUG] JSON PARSEADO COM SUCESSO: {dados_json}")
            
            # Tratamento do numero_patrimonio
            if not dados_json.get("numero_patrimonio"):
                dados_json["numero_patrimonio"] = f"AUTO-{str(uuid.uuid4())[:6].upper()}"
                print(f"--- [DEBUG] GERADO CÓDIGO AUTOMÁTICO: {dados_json['numero_patrimonio']}")

            # Preparando para salvar
            item_para_salvar = PatrimonioCreate(**dados_json)
            
            # CHAMADA DE SALVAMENTO
            print("--- [DEBUG] TENTANDO SALVAR NO BANCO DE DADOS... ---")
            novo_item = criar_patrimonio(item=item_para_salvar, db=db)
            
            # SE CHEGAR AQUI, SALVOU
            print(f"--- [DEBUG] SUCESSO! ID GERADO: {novo_item.id} ---")
            
            return {
                "type": "success", 
                "message": f"Certo! Item '{novo_item.nome}' ({novo_item.numero_patrimonio}) registrado.",
                "data": {
                    "id": novo_item.id,
                    "numero_patrimonio": novo_item.numero_patrimonio,
                    "nome": novo_item.nome,
                    "sala": novo_item.sala,
                    "quantidade": novo_item.quantidade,
                    "valor": novo_item.valor
                }
            }

        except json.JSONDecodeError:
            print("--- [DEBUG] ERRO: A IA não retornou um JSON válido.")
            return {"type": "chat", "message": "Entendi que você quer cadastrar, mas não consegui entender os dados. Tente reformular."}
        
        except Exception as e:
            # AQUI VAI APARECER O ERRO REAL
            print(f"--- [DEBUG] ERRO FATAL AO SALVAR: {e}")
            traceback.print_exc() # Imprime o erro completo no terminal
            return {"type": "error", "message": f"Erro interno ao salvar: {str(e)}"}

    else:
        # Chat normal
        print("--- [DEBUG] MODO CONVERSA NORMAL ---")
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