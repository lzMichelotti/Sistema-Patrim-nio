# Sistema de Patrimônio - LAMIC

Sistema web para gestão e controle de patrimônio e inventário, desenvolvido com **React** no frontend e **FastAPI (Python)** no backend. O sistema permite o cadastro, listagem, edição e remoção de ativos, além de funcionalidades avançadas como exportação de relatórios e um assistente de IA para cadastro rápido via chat.

## 🚀 Funcionalidades

- **Gestão de Ativos (CRUD):**
  - Cadastro de patrimônios com Número, Nome, Sala, Quantidade e Valor.
  - Edição e Exclusão de registros.
  - Visualização em lista com busca e filtragem em tempo real.

- **Relatórios:**
  - 📊 **Exportação para Excel:** Gera uma planilha `.xlsx` com o inventário atual.
  - 📄 **Exportação para PDF:** Gera um relatório formatado em PDF pronto para impressão.

- **🤖 Assistente IA (ChatWidget):**
  - Integração com **Google Gemini AI**.
  - Permite cadastrar itens usando linguagem natural (ex: *"Cadastre 10 cadeiras na sala 302 no valor de 150 reais cada"*).
  - A IA extrai os dados automaticamente e realiza o cadastro no banco.

## 🛠 Tecnologias Utilizadas

### Backend
- **Python 3**
- **FastAPI**: Framework web rápido e moderno.
- **SQLAlchemy**: ORM para interação com banco de dados (SQLite por padrão, suporta MySQL).
- **Pydantic**: Validação de dados.
- **Pandas / OpenPyXL**: Manipulação e exportação de dados para Excel.
- **ReportLab**: Geração de PDFs.
- **Google GenAI SDK**: Integração com a IA do Google Gemini.

### Frontend
- **React (Vite)**: Biblioteca para construção da interface de usuário.
- **CSS3**: Estilização responsiva.

### Infraestrutura (Opcional)
- **Docker & Docker Compose**: Para orquestração de contêineres (inclui configuração para MySQL).

## 📋 Pré-requisitos

Certifique-se de ter instalado em sua máquina:
- **Python 3.10+**
- **Node.js** (v18+) e **npm**
- Uma chave de API do Google (para usar o chat com IA).

## 🔧 Instalação e Execução

### 1. Configuração do Backend

1. Navegue até a pasta `backend`:
   ```bash
   cd backend
   ```

2. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   # No Linux/Mac:
   source venv/bin/activate
   # No Windows:
   venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na pasta `backend` com o seguinte conteúdo:
     ```env
     GOOGLE_API_KEY="sua_chave_aqui"
     # Opcional: Se for usar MySQL
     # DATABASE_URL="mysql+pymysql://user:password@localhost/patrimonio_db"
     ```

5. (Opcional) Verifique os modelos Gemini disponíveis:
   ```bash
   python testes_modelos.py
   ```

6. Inicie o servidor:
   ```bash
   uvicorn main:app --reload
   ```
   *O backend rodará em: `http://127.0.0.1:8000`*

### 2. Configuração do Frontend

1. Abra um novo terminal e navegue até a pasta `frontend`:
   ```bash
   cd frontend
   ```

2. Instale as dependências do Node:
   ```bash
   npm install
   ```

3. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```
   *O frontend rodará em: `http://localhost:5173`.*

### 3. Execução com Docker (Opcional)

Se preferir rodar o banco de dados MySQL via Docker:

1. Na raiz do projeto, execute:
   ```bash
   docker-compose up -d
   ```
   *Isso subirá um contêiner MySQL na porta 3306.*

## 📂 Estrutura do Projeto

```
/
├── backend/
│   ├── main.py           # Arquivo principal da API e Rotas
│   ├── models.py         # Modelos do banco de dados (SQLAlchemy)
│   ├── database.py       # Configuração da conexão com banco
│   ├── testes_modelos.py # Script utilitário para listar modelos Gemini
│   └── patrimonio.db     # Banco de dados SQLite (gerado automaticamente)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Componente principal e lógica da UI
│   │   └── components/
│   │       └── ChatWidget.jsx # Componente do Chat com IA
│   └── package.json
└── docker-compose.yml    # Configuração do Docker para MySQL
```

## 🤝 Contribuição

Sinta-se à vontade para abrir issues ou enviar pull requests para melhorias no projeto.
