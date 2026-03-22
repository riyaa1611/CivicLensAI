# CivicLens

CivicLens is an AI-powered civic intelligence platform that makes Indian government policies and legislation accessible to everyone. It continuously ingests bills, press releases, and gazette notifications, indexes them with vector embeddings, and lets users ask plain-English questions — returning grounded answers with cited sources.

---

## Features

- **Policy Q&A** — Ask natural language questions about Indian laws and regulations and get accurate, source-backed answers
- **Automatic Ingestion** — Scheduled scraping from PRS India, PIB, and the Official Gazette every 6 hours
- **Document Upload** — Upload bills or policy PDFs directly for instant analysis and indexing
- **Policy Feed** — Browse, search, and filter the latest ingested policies with AI-generated summaries and tags
- **Context Optimization** — Retrieved policy chunks are compressed before the LLM call to reduce token usage while preserving answer quality
- **Dashboard** — Live metrics on indexed policies, queries answered, and compression stats

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API framework
- SQLite via SQLAlchemy — relational storage for policies and query logs
- [FAISS](https://github.com/facebookresearch/faiss) — local vector index (Pinecone cloud optional)
- `BAAI/bge-small-en-v1.5` — 384-dim sentence embeddings via `sentence-transformers`
- [ScaleDown](https://scaledown.xyz) — context compression API (optional, reduces LLM token usage)
- [APScheduler](https://apscheduler.readthedocs.io/) — background ingestion scheduler
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF text extraction
- LLM via [OpenRouter](https://openrouter.ai/) — configurable model for Q&A and summarization

**Frontend**
- [React 18](https://react.dev/) + TypeScript
- [Vite](https://vitejs.dev/) — build tooling
- [TailwindCSS](https://tailwindcss.com/) — styling
- [TanStack Query](https://tanstack.com/query) — server state management
- [React Router v6](https://reactrouter.com/) — client-side routing

---

## Project Structure

```
CivicLens_V2/
├── backend/
│   └── civiclens/
│       ├── api/            # FastAPI routes and server entrypoint
│       ├── config/         # App settings (Pydantic)
│       ├── db/             # SQLAlchemy models and database setup
│       ├── embeddings/     # Embedding generation (BGE model)
│       ├── ingestion/      # Scrapers: PRS, PIB, Gazette, Gov Schemes
│       ├── llm/            # LLM analyzer and policy classifier
│       ├── optimization/   # Context compression pipeline
│       ├── processing/     # Text cleaning and PDF extraction
│       ├── retrieval/      # Vector search and retriever
│       ├── services/       # Business logic: policy and query services
│       └── vectorstore/    # Pinecone + FAISS vector store abstraction
├── frontend/
│   └── src/
│       ├── components/     # Reusable UI components
│       ├── pages/          # Route-level pages
│       ├── services/       # API client
│       └── types/          # TypeScript type definitions
├── start_backend.bat
├── start_frontend.bat
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai/) API key (required)
- A [Pinecone](https://www.pinecone.io/) account (optional — FAISS used by default)
- A [ScaleDown](https://scaledown.xyz) API key (optional — enables compression analytics)

### Environment Setup

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and set at minimum:
- `OPENROUTER_API_KEY` — get one free at [openrouter.ai/keys](https://openrouter.ai/keys)
- All other keys are optional (Pinecone falls back to FAISS, ScaleDown compression is disabled if unset)

See [.env.example](.env.example) for a full list of variables with descriptions.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn civiclens.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and the API at `http://localhost:8000`.

On Windows, you can use the provided batch scripts:

```
start_backend.bat
start_frontend.bat
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/policies` | List all ingested policies |
| `GET` | `/api/v1/policy/{id}` | Get a single policy by ID |
| `POST` | `/api/v1/query` | Ask a question, returns answer + sources |
| `POST` | `/api/v1/upload` | Upload a policy PDF for ingestion |
| `POST` | `/api/v1/ingest` | Trigger manual ingestion run |
| `GET` | `/api/v1/dashboard` | System metrics and compression stats |
| `POST` | `/api/v1/admin/rescan` | Re-summarize policies with missing summaries |
| `POST` | `/api/v1/admin/reindex` | Re-embed all policies into the vector store |

Full interactive docs available at `http://localhost:8000/docs`.

---

## Data Sources

| Source | Description |
|--------|-------------|
| [PRS India](https://prsindia.org/billtrack) | Parliamentary bills and legislative summaries |
| [PIB](https://pib.gov.in/) | Press Information Bureau press releases |
| [Gazette of India](https://egazette.gov.in/) | Official government notifications |
| Manual Upload | User-uploaded PDF bills and policy documents |

---

## License

MIT License. See [LICENSE](LICENSE) for details.
