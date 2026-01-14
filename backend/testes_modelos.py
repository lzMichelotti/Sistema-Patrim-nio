import google.genai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração da API do Gemini
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("--- Buscando modelos disponíveis para sua chave ---")
try:
    for m in client.models.list():
        print(f"- {m.name}")
except Exception as e:
    print(f"Erro ao listar: {e}")