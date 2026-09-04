# Multi-Agent RAG Document Q&A

A complete personal-project implementation of a stateful, cited document Q&A system. A LangGraph coordinator classifies each question and routes it to a specialist retrieval agent. Documents are parsed, chunked, embedded with OpenAI, and stored in Pinecone. The React workspace supports uploads, document filtering, streaming-style answers, source inspection, and conversation history.

## Architecture

`React -> FastAPI/Lambda -> LangGraph coordinator -> specialist agent -> Pinecone -> OpenAI -> cited answer`

Specialists: `technical`, `financial`, and `general`. The selected specialist and retrieved citations are returned with every answer.

## Quick start (demo mode)

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:5173. Demo mode needs no API keys and ships with a small in-memory corpus.

## Run with OpenAI + Pinecone

Set `DEMO_MODE=false`, add the three credentials in `.env`, then:

```bash
docker compose up --build
```

Create a Pinecone serverless index with dimension `1536` and cosine similarity. The API can also create it when the account permits.

## Local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## API

- `POST /api/documents` — upload PDF, DOCX, TXT, or Markdown
- `GET /api/documents` — list indexed documents
- `DELETE /api/documents/{id}` — remove one document
- `POST /api/chat` — ask a cited question
- `GET /health` — dependency-aware health check

## AWS Lambda

The backend includes an AWS SAM template and Mangum adapter:

```bash
sam build
sam deploy --guided
```

For production, put secrets in AWS Secrets Manager or encrypted Lambda environment variables, restrict CORS, enable API Gateway authorization, and provision the Pinecone index before deployment.

## Tests

```bash
cd backend && pytest
cd frontend && npm run build
```

## Design notes

- The graph state keeps query, conversation history, route, retrieved chunks, answer, and citations explicit.
- Retrieval is filtered by specialist and optional document IDs.
- Citations are generated from retrieved metadata rather than model-created references.
- Files are validated for type and size; temporary files are not retained.
- Demo and production providers share the same service interfaces.

