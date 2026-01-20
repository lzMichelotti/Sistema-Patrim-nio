from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import google.genai as genai
import json
import os
from dotenv import load_dotenv
import uuid 
import traceback 

# Importações dos módulos refatorados
from database import engine, get_db, Base
from models import SALA_MODELS, get_model_for_sala
from salas import SALAS
import unicodedata

load_dotenv()

# --- Inicialização do Banco de Dados ---
# Cria as tabelas no banco automaticamente se não existirem
Base.metadata.create_all(bind=engine)

# --- Schemas (Pydantic) ---
# Classes para validação de dados que entram e saem da API
class PatrimonioCreate(BaseModel):
    numero_patrimonio_lamic: str | None = None
    numero_patrimonio_ufsm: str | None = None
    nome: str
    sala: str
    quantidade: int
    valor_total: float

    class Config:
        json_schema_extra = {
            "example": {
                "numero_patrimonio_lamic": "LAMIC-001",
                "numero_patrimonio_ufsm": "UFSM-2024-001",
                "nome": "Micropipeta",
                "sala": "Preparação",
                "quantidade": 1,
                "valor_total": 1500.00
            }
        }


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
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rotas da API ---

@app.get("/salas/")
def listar_salas():
    """Retorna a lista de salas disponíveis"""
    return {"salas": SALAS}

def _normalize_sala_name(raw: str) -> str:
    """Normaliza texto livre para casar com a lista de SALAS."""
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower().strip()

    # remove artigos/preposições comuns e a palavra 'sala'
    replacements = [
        "sala dos ", "sala das ", "sala do ", "sala da ", "sala de ", "sala ",
        "dos ", "das ", "do ", "da ", "de "
    ]
    for rep in replacements:
        if lowered.startswith(rep):
            lowered = lowered[len(rep):].strip()

    # espaços duplos para simples
    lowered = " ".join(lowered.split())
    return lowered


_SALA_LOOKUP = { _normalize_sala_name(s): s for s in SALAS }


def _resolve_sala(raw: str) -> str:
    key = _normalize_sala_name(raw)
    if key in _SALA_LOOKUP:
        return _SALA_LOOKUP[key]
    raise HTTPException(status_code=400, detail=f"Sala inválida: {raw}")


def _safe_get_model(sala: str):
    resolved = _resolve_sala(sala)
    return get_model_for_sala(resolved)


def _listar_todos(db: Session):
    itens = []
    for sala, model in SALA_MODELS.items():
        registros = db.query(model).all()
        for reg in registros:
            # Adiciona explicitamente a sala para resposta consistente
            reg.sala = sala
        itens.extend(registros)
    return itens


@app.post("/patrimonios/", response_model=PatrimonioResponse)
def criar_patrimonio(item: PatrimonioCreate, db: Session = Depends(get_db)):
    sala_resolvida = _resolve_sala(item.sala)
    model = get_model_for_sala(sala_resolvida)
    payload = item.dict()
    payload["sala"] = sala_resolvida
    db_item = model(**payload)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/patrimonios/", response_model=list[PatrimonioResponse])
def listar_patrimonios(db: Session = Depends(get_db)):
    return _listar_todos(db)


@app.put("/patrimonios/{sala}/{id}", response_model=PatrimonioResponse)
def atualizar_patrimonio(sala: str, id: int, item: PatrimonioCreate, db: Session = Depends(get_db)):
    sala_resolvida = _resolve_sala(sala)
    model = get_model_for_sala(sala_resolvida)
    db_item = db.query(model).filter(model.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    for key, value in item.dict().items():
        if key == "sala":
            value = sala_resolvida
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/patrimonios/{sala}/{id}")
def deletar_patrimonio(sala: str, id: int, db: Session = Depends(get_db)):
    sala_resolvida = _resolve_sala(sala)
    model = get_model_for_sala(sala_resolvida)
    item = db.query(model).filter(model.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    db.delete(item)
    db.commit()
    return {"mensagem": "Item deletado com sucesso"}

# --- Rotas de Relatórios ---

@app.get("/exportar_excel")
def exportar_excel(db: Session = Depends(get_db)):
    items = _listar_todos(db)

    dados = []
    for item in items:
        dados.append({
            "Patrimônio LAMIC": item.numero_patrimonio_lamic,
            "Patrimônio UFSM": item.numero_patrimonio_ufsm or "",
            "Nome/Descrição": item.nome,
            "Sala": item.sala,
            "Quantidade": item.quantidade,
            "Valor Total (R$)": item.valor_total
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
    items = _listar_todos(db)
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=1.5*cm,
    )
    elements = []

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=8,
        alignment=1,
        fontName='Helvetica-Bold'
    )

    subtitulo_style = ParagraphStyle(
        'SubTituloCustom',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=1,
        spaceAfter=18
    )

    sala_style = ParagraphStyle(
        'SalaCustom',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#1a5490'),
        borderWidth=1,
        borderPadding=6
    )

    desc_style = ParagraphStyle(
        'DescCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#222222')
    )

    header_data = []
    try:
        logo_lamic = Image('logo_lamic.png', width=2*cm, height=1.5*cm)
        logo_ufsm = Image('ufsm_png.png', width=2*cm, height=1.5*cm)
        header_data = [[logo_lamic,
                        Paragraph("Relatório de Patrimônio<br/><b>LAMIC - Laboratório de Análises Micotoxicológicas</b>", titulo_style),
                        logo_ufsm]]
    except:
        header_data = [[Paragraph("Relatório de Patrimônio<br/><b>LAMIC - Laboratório de Análises Micotoxicológicas</b>", titulo_style)]]

    header_table = Table(header_data, colWidths=[2.5*cm, 12*cm, 2.5*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(header_table)
    elements.append(Paragraph(f"<font size=9 color='#666666'>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</font>", subtitulo_style))
    elements.append(Spacer(1, 0.25*cm))

    separator = Table([['']], colWidths=[18*cm])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#1a5490')),
    ]))
    elements.append(separator)
    elements.append(Spacer(1, 0.4*cm))

    itens_por_sala = {}
    for item in items:
        itens_por_sala.setdefault(item.sala, []).append(item)

    salas_ordenadas = sorted(itens_por_sala.keys())

    for sala in salas_ordenadas:
        elements.append(Paragraph(f"<b>{sala}</b>", sala_style))

        data = [['Patr. LAMIC', 'Patr. UFSM', 'Descrição/Nome', 'Qtd', 'Valor Total (R$)']]

        total_valor = 0
        for item in itens_por_sala[sala]:
            desc_para = Paragraph(item.nome, desc_style)
            data.append([
                item.numero_patrimonio_lamic,
                item.numero_patrimonio_ufsm or "-",
                desc_para,
                str(item.quantidade),
                f"R$ {item.valor_total:.2f}"
            ])
            total_valor += item.valor_total

        data.append(['', '', 'TOTAL SALA:', '', f'R$ {total_valor:.2f}'])

        table = Table(
            data,
            colWidths=[2.8*cm, 3.2*cm, 9.0*cm, 1.2*cm, 2.5*cm],
            repeatRows=1,
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 1), (1, -2), 'CENTER'),
            ('ALIGN', (2, 1), (2, -2), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),
            ('VALIGN', (0, 1), (-1, -2), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -2), 0.3, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f3f4f6')]),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0f7')),
            ('ALIGN', (2, -1), (2, -1), 'RIGHT'),
            ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.35*cm))

    elements.append(Spacer(1, 0.45*cm))
    footer_separator = Table([['']], colWidths=[18*cm])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#1a5490')),
    ]))
    elements.append(footer_separator)

    total_geral = sum(item.valor_total for item in items)
    footer_text = f"<font size=9 color='#666666'><b>Total Geral de Patrimônio:</b> R$ {total_geral:.2f} | <b>Total de Itens:</b> {len(items)}</font>"
    elements.append(Paragraph(footer_text, subtitulo_style))

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
        - Campos obrigatórios: nome (string), sala (string), quantidade (int), valor_total (float).
        - Campos opcionais: numero_patrimonio_lamic (string) e numero_patrimonio_ufsm (string). Se o usuário disser (ex: "código X", "patrimônio Y"), extraia. Se não, deixe null.
        - O valor_total deve ser numérico (ex: 1200.50), sem R$.
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
            dados_json = json.loads(texto_limpo)
            
            if not dados_json.get("numero_patrimonio_lamic"):
                dados_json["numero_patrimonio_lamic"] = f"AUTO-{str(uuid.uuid4())[:6].upper()}"

            dados_json["sala"] = _resolve_sala(dados_json.get("sala", ""))

            item_para_salvar = PatrimonioCreate(**dados_json)

            model = get_model_for_sala(item_para_salvar.sala)
            db_item = model(**item_para_salvar.dict())
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            
            print(f"--- [DEBUG] SUCESSO! ID GERADO: {db_item.id} ---")
            
            return {
                "type": "success", 
                "message": f"Certo! Item '{db_item.nome}' ({db_item.numero_patrimonio_lamic}) registrado.",
                "data": {
                    "id": db_item.id,
                    "numero_patrimonio_lamic": db_item.numero_patrimonio_lamic,
                    "nome": db_item.nome,
                    "sala": db_item.sala,
                    "quantidade": db_item.quantidade,
                    "valor_total": db_item.valor_total
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
