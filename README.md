# Sistema de Patrimonio

Sistema simples para controle de patrimonio com:

- Backend em FastAPI
- Frontend em React
- Banco SQLite

A opção de ser SQLite foi porque o sistema tem pouco acesso e poucas alteracoes, e queriamos a opção mais leve possivel.

## Tecnologias usadas

- FastAPI: API REST do backend.
- SQLAlchemy: camada de acesso ao banco.
- SQLite: banco de dados local e em producao (mais leve).
- React: interface web.
- Vite: build e servidor de desenvolvimento do frontend.
- Docker e Docker Compose: execucao e deploy dos servicos.
- Nginx: entrega do frontend e proxy para o backend.


## Rodar com Docker

1. Copie `.env.docker` para `.env` na raiz.
2. Suba os containers:

```bash
docker compose up -d --build
```

3. (Opcional, quando precisar repovoar o banco) popular salas:

```bash
docker compose exec backend python seed.py
```

4. (Opcional) popular salas + itens padrao em todas as salas:

```bash
docker compose exec backend python seed.py --com-itens
```

## Acessos

- Frontend: `http://localhost:8090`
- Backend: `http://localhost:8010`
- Docs da API: `http://localhost:8010/docs`

## Rodar local (sem Docker)

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Popular salas localmente:

```bash
python seed.py
```

Popular salas + itens padrao localmente:

```bash
python seed.py --com-itens
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
