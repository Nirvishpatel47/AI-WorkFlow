# AI WorkFlow — Intelligent Document Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC143C?style=flat-square)](https://qdrant.tech)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

> **Chat with your documents using production-grade RAG.** Upload PDFs, spreadsheets, codebases, emails, and more — then ask natural-language questions and get grounded, context-aware answers powered by Google Gemini and semantic vector search.

## Live Workspace

[![Open Smart AI](https://img.shields.io/badge/Launch-Smart_AI_Workspace-111111?style=for-the-badge&logo=render&logoColor=white)](https://ai-workflow-y1ka.onrender.com)
---

## What Problem Does This Solve?

Knowledge workers, developers, and researchers routinely drown in unstructured documents: API specs, research papers, email threads, codebases, financial spreadsheets. Traditional keyword search breaks down on nuanced questions; generic LLM chatbots hallucinate when they lack grounded source material.

**DocuMind bridges that gap.** It lets users upload their own private document corpus and have real, grounded conversations with it — without their data ever leaving their control. The system uses a multi-stage RAG (Retrieval-Augmented Generation) pipeline with sub-query decomposition, HyDE (Hypothetical Document Embeddings), and semantic chunking to deliver answers that are accurate, contextual, and traceable.

### Who Is This For?

| User Type | Use Case |
|-----------|----------|
| **Developers** | Chat with codebase documentation, API specs, and architecture docs |
| **Researchers** | Query across multiple research papers and generate synthesis answers |
| **Legal & Finance** | Extract insights from contracts, reports, and regulatory filings |
| **Support Teams** | Onboard new hires by letting them query internal knowledge bases |
| **Students** | Upload lecture notes and textbooks to get personalized explanations |

---

## Features

- **Multi-format document ingestion** — PDF (markdown-fidelity extraction), DOCX, XLSX/CSV, EML emails, and 40+ code file extensions
- **Advanced RAG pipeline** — sub-query decomposition → HyDE retrieval → semantic deduplication → grounded synthesis
- **Semantic chunking** — lightweight Jaccard-similarity chunker with no external ML model dependency; also supports code-aware splitting by language
- **Multi-tenant isolation** — all vector searches, caches, and database queries are hard-filtered by `user_id` at the engine layer
- **Persistent chat history** — conversation context is maintained across sessions via PostgreSQL, and the last N turns are condensed into coherent search queries
- **Redis caching layer** — document metadata, vector query results, and token blacklists are all cached to minimize latency and database pressure
- **JWT authentication** — stateless token issuance with server-side revocation via Redis token blacklists
- **Rate limiting** — per-endpoint rate limits enforced via `fastapi-limiter` backed by Redis
- **Argon2 password hashing** — industry-standard memory-hard hashing; no plaintext or MD5/bcrypt shortcuts
- **Secret management** — all credentials fetched from Doppler at runtime; no `.env` files in production
- **Structured logging** — rotating file + console logger with function-level context and full tracebacks
- **Load testing suite** — Locust-based test harness with full user lifecycle simulation

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | FastAPI 0.112 | Async HTTP server, routing, dependency injection |
| **LLM** | Google Gemini 2.5 Flash Lite | Chat completion, sub-query generation, HyDE |
| **Embeddings** | Gemini Embedding 2 (3072-dim) | Dense vector generation for semantic search |
| **Vector Database** | Qdrant | Cosine similarity search with payload filtering |
| **Relational DB** | PostgreSQL (SQLAlchemy 2.0) | Users, documents, and chat history |
| **Cache / Session** | Redis (async) | Metadata cache, token blacklist, rate limiting, chat history |
| **Secret Management** | Doppler | Runtime secret injection; OS env fallback |
| **Auth** | python-jose JWT + Argon2 | Stateless auth with server-side revocation |
| **File Parsing** | PyMuPDF4LLM, python-docx, openpyxl, BeautifulSoup | Format-specific extraction |
| **Rate Limiting** | fastapi-limiter | Redis-backed per-route throttling |
| **Load Testing** | Locust | Simulated multi-user RAG workload |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTPS  Bearer JWT
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                           │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │ RateLimiter │  │  JWT Decoder  │  │  Cache-Control ASGI  │    │
│  │ (Redis)     │  │  (Dependency) │  │  Middleware           │   │
│  └─────────────┘  └───────────────┘  └──────────────────────┘    │
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐                   │
│  │  /addDocument    │     │  /chat           │                   │
│  │  Upload → Parse  │     │  Query → RAG     │                   │
│  │  → Chunk → Embed │     │  Pipeline        │                   │
│  └────────┬─────────┘     └────────┬─────────┘                   │
└───────────┼────────────────────────┼────────────────────────────┘
            │                        │
   ┌────────▼────────┐       ┌───────▼───────────────────────────┐
   │  Files_Parser   │       │        RAG Pipeline               │
   │                 │       │                                   │
   │  .pdf → MD      │       │  1. Condense conversation history │
   │  .docx → text   │       │  2. Decompose into sub-queries    │
   │  .xlsx/.csv     │       │  3. Generate HyDE docs per query  │
   │  .eml → plain   │       │  4. Vector search (per sub-query) │
   │  40+ code exts  │       │  5. Deduplicate + rank results    │
   └────────┬────────┘       │  6. Synthesise final answer       │
            │                └────────┬──────────────────────────┘
   ┌────────▼────────┐                │
   │   Chunker       │       ┌────────▼──────────┐
   │                 │       │   Gemini API      │
   │ Semantic chunks │       │   (Flash Lite +   │
   │ Code-aware split│       │   Embedding 2)    │
   └────────┬────────┘       └────────┬──────────┘
            │                         │
   ┌────────▼─────────────────────────▼───────────┐ 
   │                  Qdrant                      │
   │   Collection: "documents"                    │
   │   Payload index: user_id, document_id        │
   │   3072-dim Cosine vectors                    │
   └──────────────────────────────────────────────┘

   ┌──────────────────┐    ┌──────────────────────┐
   │   PostgreSQL     │    │       Redis          │
   │                  │    │                      │
   │  users           │    │  user_docs_meta:{id} │
   │  documents       │    │  chat:{id}:history   │
   │  chat_history    │    │  blacklist:{token}   │
   └──────────────────┘    │  Rate limit counters │
                           └──────────────────────┘
```

### RAG Pipeline Deep-Dive

The `/chat` endpoint executes a five-stage pipeline before any answer is generated:

**Stage 1 — History Condensation.** The last 10 chat turns are loaded from PostgreSQL and summarised into a single coherent search query. This ensures follow-up questions like *"What about the second approach?"* resolve correctly against document context.

**Stage 2 — Sub-Query Decomposition.** The condensed query is sent to Gemini with a strict JSON-output prompt to break complex questions into 2–3 atomic retrieval targets (e.g., *"How does authentication work?"* → `["JWT token structure", "token revocation mechanism", "session expiry policy"]`).

**Stage 3 — HyDE (Hypothetical Document Embeddings).** For each sub-query, Gemini generates a short *hypothetical* passage that would perfectly answer it. This synthetic document is then embedded and used as the search vector. HyDE consistently outperforms raw query embedding on technical and domain-specific corpora.

**Stage 4 — Vector Retrieval & Deduplication.** Each HyDE embedding is searched against Qdrant with a hard `user_id` filter. Results across all sub-queries are deduplicated by exact text match and capped at 4 unique context windows.

**Stage 5 — Grounded Synthesis.** Retrieved context, conversation history, and the original user question are assembled into a final prompt and sent to Gemini Flash Lite for answer generation.

---

## Project Structure

```
.
├── Frontend_Connection.py          # FastAPI application — routes, middleware, lifespan
│
├── Files_Management/
│   └── Files_Parser.py             # FileParser, ParseFile router, Chunker (semantic + code)
│
├── RAG/
│   ├── EmbeddingsGenerationnStorage.py  # EmbeddingsALL — ingestion + answer pipeline
│   ├── Gemini_Api_connection.py    # Gemini client wrapper (chat + embeddings)
│   └── Vector_Store.py             # Qdrant client wrapper — CRUD + search
│
├── DATABASE/
│   ├── SQL_Database.py             # SQLAlchemy UserConnection — all SQL operations
│   └── Redis_Connection.py         # RedisCacheManager — async cache, history, blacklist
│
├── Security/
│   ├── JWT_token.py                # JWT creation and decoding (python-jose)
│   ├── Advance_Logger.py           # Rotating file + console logger
│   └── get_secretes.py             # Doppler secret fetcher with OS env fallback
│
├── static/                         # Served as /static — CSS, JS assets (1-day cache TTL)
├── templates/                      # Jinja-less HTML templates served directly
│   ├── landing.html
│   ├── login.html
│   ├── signin.html
│   ├── dashboard.html
│   ├── chat.html
│   └── settings.html
│
├── locustfile.py                   # Load testing — full user lifecycle simulation
├── requirements.txt
└── pyproject.toml
```

---

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Qdrant Cloud account (or self-hosted instance)
- Google AI Studio API key (Gemini access)
- Doppler account (or substitute with OS environment variables)

### Clone & Install

```bash
git clone https://github.com/your-org/documind.git
cd documind

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Environment Variables

All secrets are fetched from Doppler at startup via `get_secretes.py`. If Doppler is not configured, the system falls back to OS environment variables.

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection string | `postgresql://user:pass@localhost/documind` |
| `REDIS_HOST` | Redis connection URL | `redis://localhost:6379` |
| `QDRANT_URL` | Qdrant instance URL | `https://your-cluster.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant API key | `your-qdrant-api-key` |
| `GEMINI_API_KEY` | Google AI Studio API key | `AIza...` |
| `JWT_SECRETE` | JWT signing secret (min 32 chars) | `your-strong-random-secret` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `DOPPLER_TOKEN` | Doppler service token (if using Doppler) | `dp.st.prod...` |
| `DOPPLER_PROJECT` | Doppler project name | `documind` |
| `DOPPLER_CONFIG` | Doppler config name | `production` |

### Doppler Setup (Recommended)

```bash
# Install Doppler CLI
brew install dopplerhq/cli/doppler        # macOS
# or see https://docs.doppler.com/docs/install-cli for other platforms

doppler login
doppler setup --project documind --config production

# Inject secrets at runtime
doppler run -- uvicorn Frontend_Connection:app --host 0.0.0.0 --port 8000
```

### Without Doppler

```bash
export DATABASE_URL="postgresql://user:pass@localhost/documind"
export REDIS_HOST="redis://localhost:6379"
export QDRANT_URL="https://..."
export QDRANT_API_KEY="..."
export GEMINI_API_KEY="AIza..."
export JWT_SECRETE="your-strong-random-secret-min-32-chars"
export JWT_ALGORITHM="HS256"
```

---

## Configuration

### Rate Limits

Configured directly on route decorators in `Frontend_Connection.py`:

| Endpoint | Limit |
|----------|-------|
| `POST /login` | 5 requests / 60 seconds |
| `POST /signin` | 3 requests / 60 seconds |
| `POST /addDocument` | 5 requests / 60 seconds |
| `POST /chat` | 10 requests / 60 seconds |

### File Upload Constraints

```python
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB per file

BLACKLISTED_EXTENSIONS = {
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.bz2', '.xz', '.z', '.exe'
}
```

### Chunking Parameters

```python
# Sliding window (plain text / fallback)
chunk_size    = 1200   # characters
chunk_overlap = 200    # characters

# Semantic chunker
similarity_threshold = 0.07   # Jaccard similarity split threshold
min_chunk_size       = 800    # Minimum chars before a split is allowed
```

### Vector Store

```python
COLLECTION_NAME = "documents"
VECTOR_SIZE     = 3072        # Gemini Embedding 2 output dimension
DISTANCE        = Distance.COSINE
```

---

## Running Locally

```bash
# Start dependencies (example with Docker Compose)
docker compose up -d postgres redis

# Run database migrations (tables are auto-created on startup)
python -m DATABASE.SQL_Database

# Start the server
uvicorn Frontend_Connection:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at `http://localhost:8000`.

On startup, the lifespan handler:
1. Initialises the Redis connection pool
2. Registers the pool with `FastAPILimiter`
3. Auto-creates PostgreSQL tables if they don't exist
4. Verifies/creates the Qdrant collection and payload indexes

---

## Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "Frontend_Connection:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DOPPLER_TOKEN=${DOPPLER_TOKEN}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: documind
      POSTGRES_USER: documind
      POSTGRES_PASSWORD: documind
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

## API Documentation

FastAPI auto-generates interactive docs at `/docs` (Swagger UI) and `/redoc`.

### Authentication

All protected endpoints require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Tokens are valid for **7 days** and are revoked server-side on logout via Redis blacklisting.

---

### Endpoints

#### `POST /signin`
Create a new user account.

```bash
curl -X POST http://localhost:8000/signin \
  -F "name=Jane Doe" \
  -F "email=jane@example.com" \
  -F "password=SecurePass123"
```

**Response:**
```json
{
  "success": true,
  "message": "sign-in successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": 1, "name": "Jane Doe", "email": "jane@example.com" }
}
```

---

#### `POST /login`
Authenticate an existing user.

```bash
curl -X POST http://localhost:8000/login \
  -F "email=jane@example.com" \
  -F "password=SecurePass123"
```

---

#### `POST /addDocument`
Upload one or more documents for processing and embedding.

```bash
curl -X POST http://localhost:8000/addDocument \
  -H "Authorization: Bearer <token>" \
  -F "files=@report.pdf" \
  -F "files=@data.xlsx"
```

**Response:**
```json
{
  "success": true,
  "uploaded": ["report.pdf", "data.xlsx"],
  "failed": []
}
```

Pipeline: `upload → temp file → parse → semantic chunk → embed → Qdrant upsert → SQL metadata insert → Redis cache invalidation`

---

#### `POST /show_documents`
List all documents uploaded by the authenticated user.

```bash
curl -X POST http://localhost:8000/show_documents \
  -H "Authorization: Bearer <token>"
```

Responses are cached in Redis for **600 seconds**. Cache is invalidated on upload or deletion.

---

#### `POST /delete_document?Document_id=<id>`
Delete a document and all associated vectors.

```bash
curl -X POST "http://localhost:8000/delete_document?Document_id=42" \
  -H "Authorization: Bearer <token>"
```

Performs: SQL row deletion → Qdrant vector deletion (filtered by `document_id` AND `user_id`) → Redis cache invalidation.

---

#### `POST /chat`
Ask a question against the user's document corpus.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <token>" \
  -F "query=What are the key findings in the Q3 report?"
```

**Response:**
```json
{
  "success": true,
  "message": "The Q3 report highlights three key findings: ..."
}
```

---

#### `POST /logout`
Revoke the current JWT token.

```bash
curl -X POST http://localhost:8000/logout \
  -H "Authorization: Bearer <token>"
```

The token is stored in Redis with a 7-day TTL (`blacklist:<token>` key), matching the JWT expiry window.

---

## Database Schema Overview

### `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `name` | TEXT | NOT NULL |
| `email` | TEXT | UNIQUE NOT NULL |
| `password` | TEXT | NOT NULL (Argon2 hash) |

### `documents`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `user_id` | INTEGER | FK → users(id) ON DELETE CASCADE |
| `file_name` | TEXT | NOT NULL |
| `extension` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### `chat_history`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `user_id` | INTEGER | FK → users(id) ON DELETE CASCADE |
| `role` | TEXT | `"user"` or `"model"` |
| `message` | TEXT | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**Index:** `idx_chat_history_user_date ON chat_history(user_id, created_at DESC)` — optimises the "last N messages per user" access pattern.

---

## Authentication Flow

```
Client                         FastAPI                    Redis               PostgreSQL
  │                               │                         │                     │
  │  POST /signin                 │                         │                     │
  │──────────────────────────────►│                         │                     │
  │                               │  Argon2.hash(password)  │                     │
  │                               │  INSERT INTO users      │                     │
  │                               │────────────────────────────────────────────►  │
  │  { token: JWT }               │                         │                     │
  │◄──────────────────────────────│                         │                     │
  │                               │                         │                     │
  │  POST /chat                   │                         │                     │
  │  Authorization: Bearer <jwt>  │                         │                     │
  │──────────────────────────────►│                         │                     │
  │                               │  is_token_blacklisted?  │                     │
  │                               │────────────────────────►│                     │
  │                               │  false                  │                     │
  │                               │◄────────────────────────│                     │
  │                               │  jwt.decode → user_id   │                     │
  │                               │  [process request]      │                     │
  │                               │                         │                     │
  │  POST /logout                 │                         │                     │
  │──────────────────────────────►│                         │                     │
  │                               │  SET blacklist:<token>  │                     │
  │                               │  EX 604800              │                     │
  │                               │────────────────────────►│                     │
  │  { success: true }            │                         │                     │
  │◄──────────────────────────────│                         │                     │
```

> **Note:** Token blacklisting is implemented at the middleware level via `get_user_id` dependency injection. Every request to a protected endpoint checks Redis before decoding the JWT payload.

---

## File Processing Pipeline

```
Upload (multipart/form-data)
        │
        ▼
Extension check (blacklist: .zip, .exe, .rar ...)
        │
        ▼
Size check (≤ 15 MB)
        │
        ▼
Write to tempfile (OS-managed, auto-cleaned in finally block)
        │
        ▼
ParseFile.parse_any_file(temp_path)
        │
        ├── .pdf      → pymupdf4llm.to_markdown()   (layout-preserving)
        ├── .docx     → python-docx paragraph join
        ├── .eml      → BytesParser → text/plain → HTML fallback
        ├── .xlsx/.xls/.csv → openpyxl / csv.reader (row | pipe | format)
        └── 40+ code exts → raw UTF-8 read
        │
        ▼
Chunker (dispatch by extension)
        │
        ├── Code extensions → chunk_code()
        │       Brace-language aware (JS/Java/C/Rust/...)
        │       Python/Ruby: split on def/class/import boundaries
        │
        └── Text/docs → chunk_text_semantically()
                Jaccard similarity between sentence token sets
                Splits when topic diverges AND min_size exceeded
        │
        ▼
Gemini Embedding 2 (3072-dim per chunk)
        │
        ▼
Qdrant upsert (batch, each point carries user_id + document_id payload)
        │
        ▼
SQL: INSERT INTO documents (user_id, file_name, extension)
        │
        ▼
Redis: invalidate user_docs_meta:{user_id}
```

---

## Redis Cache Architecture

| Key Pattern | TTL | Contents |
|-------------|-----|----------|
| `user_docs_meta:{user_id}` | 600s | JSON list of document metadata |
| `chat:{user_id}:history` | Persistent (trimmed) | Last 10 chat turns as JSON list |
| `vector_cache:{user_id}:*` | Invalidated on upload/delete | Vector search result cache |
| `blacklist:{token}` | 604800s (7d) | Revoked JWT marker |
| Rate limit keys | Per-window | Managed by fastapi-limiter |

Chat history is stored in a Redis list with `RPUSH` + `LTRIM` (atomic pipeline), keeping exactly the last `max_limit` turns. This provides O(1) writes and O(N) reads on a bounded list.

---

## Screenshots

> _Screenshots will be added after UI finalisation._

| Page | Description |
|------|-------------|
| `/` | Landing page |
| `/login` | Login form |
| `/signin` | Registration form |
| `/dashboard` | Document management dashboard |
| `/chat` | Chat interface with document corpus |
| `/settings` | User settings |

---

## Load Testing

The included `locustfile.py` simulates full user lifecycle load:

```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

Open `http://localhost:8089` to configure and run the test.

**Simulated task weights:**

| Task | Weight | Description |
|------|--------|-------------|
| `view_documents` | 3 | `POST /show_documents` — exercises Redis cache |
| `ask_ai_chat` | 4 | `POST /chat` — exercises full RAG pipeline |
| `upload_small_document` | 1 | `POST /addDocument` — exercises ingestion pipeline |

Each virtual user registers a unique account on startup, then loops through tasks according to weight ratios with 2–5 second wait times between requests.

---

## Deployment Guide

### Production Checklist

- [ ] Set `DOPPLER_TOKEN` (or all individual env vars) in your deployment environment
- [ ] Use a production WSGI server: `uvicorn` with `--workers` behind Nginx
- [ ] Provision a managed PostgreSQL instance (RDS, Cloud SQL, Supabase, etc.)
- [ ] Use Redis Cloud or ElastiCache — not a single-node Redis in production
- [ ] Point `QDRANT_URL` to a Qdrant Cloud cluster with appropriate capacity
- [ ] Configure TLS termination at the load balancer / Nginx layer
- [ ] Set `JWT_SECRETE` to a cryptographically random 64+ character secret
- [ ] Review and tighten rate limit parameters for your expected traffic profile

### Gunicorn + Uvicorn Workers

```bash
pip install gunicorn
gunicorn Frontend_Connection:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

Worker count recommendation: `(2 × CPU cores) + 1`

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /app/static/;
        expires 1d;
        add_header Cache-Control "public, max-age=86400";
    }
}
```

---

## Performance Notes

- **Async throughout.** All I/O — Redis, Qdrant queries, Gemini API calls, file reads — are executed with `asyncio` and `run_in_executor` for CPU-bound parsing. The FastAPI event loop is never blocked.
- **Batch vector upserts.** All chunks from a single document are embedded individually but upserted to Qdrant in a single batch call to minimise round trips.
- **Redis document cache (600s TTL).** The `/show_documents` endpoint returns cached metadata on repeat calls, completely bypassing PostgreSQL.
- **HyDE improves recall.** By searching with a *hypothetical answer* rather than the raw question, retrieval recall on technical and domain-specific content is meaningfully higher than naive query embedding.
- **Chat history capped at 10 turns.** Redis list trim keeps memory bounded; PostgreSQL persists the full history for audit purposes.
- **`lru_cache` on secret loading.** `load_env_from_secret` is cached at the process level — Doppler is only called once per secret per process lifetime.
- **Static file caching.** The ASGI middleware sets `Cache-Control: public, max-age=86400` on all `/static` responses to offload repeat asset fetches to the browser.

---

## Security Notes

- **Argon2id password hashing** — resistant to GPU and ASIC brute-force attacks.
- **JWT token blacklisting** — logout is enforced server-side; token theft after logout is mitigated.
- **Multi-tenant vector isolation** — Qdrant queries always include a `must: [user_id = X]` filter at the search engine layer. A user cannot retrieve another user's document vectors regardless of query content.
- **File extension blacklist** — archives and executables are rejected before any processing begins.
- **15 MB file size cap** — prevents memory exhaustion from malicious uploads.
- **Rate limiting on all mutating endpoints** — mitigates credential stuffing, embedding abuse, and storage spam.
- **Doppler secret management** — no secrets in source code, no `.env` files committed to version control.
- **Input sanitisation in `FileParser.sanitize_text`** — strips non-alphanumeric characters from extracted text before embedding.
- **Parameterised SQL** — all database queries use SQLAlchemy `text()` with named bind parameters; no string interpolation.

> **Note on token blacklist scope:** The current implementation uses a 7-day Redis TTL matching the JWT expiry. Ensure Redis persistence (`appendonly yes`) is enabled in production so blacklisted tokens survive restarts.

---

## Scaling Considerations

| Bottleneck | Mitigation |
|------------|-----------|
| Gemini API rate limits | Implement exponential backoff + per-user embedding queue |
| Single Qdrant collection | Shard by user cohort or migrate to per-tenant collections at scale |
| PostgreSQL chat history | Partition `chat_history` by `user_id` or archive old turns to cold storage |
| Redis memory | Configure `maxmemory-policy allkeys-lru`; monitor blacklist key growth |
| File processing latency | Offload parsing + embedding to a background task queue (Celery/ARQ) |
| Multi-region | Deploy Gemini proxy + Qdrant read replicas in each region; PostgreSQL with read replicas |

---

## Roadmap

- [ ] **Background task queue** — decouple document ingestion from the HTTP request lifecycle (Celery + Redis broker)
- [ ] **Streaming chat responses** — SSE or WebSocket endpoint for real-time token streaming from Gemini
- [ ] **Document sharing** — allow users to share document collections with team members
- [ ] **Reranking** — add a cross-encoder reranking step between vector retrieval and synthesis
- [ ] **Citation grounding** — return source document references alongside answers
- [ ] **Observability** — OpenTelemetry traces for the full RAG pipeline; Grafana dashboard
- [ ] **Admin panel** — usage metrics, per-user storage quotas, and document auditing
- [ ] **OAuth2 / SSO** — Google and GitHub login alongside email/password
- [ ] **Export** — download chat history and retrieved context as PDF or Markdown

---

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository and create a feature branch: `git checkout -b feat/your-feature`
2. Ensure all changes are covered by tests or a Locust scenario update
3. Run the existing load tests against a local instance before submitting
4. Submit a pull request with a clear description of the change and its motivation

Please use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## Troubleshooting

**`Secret 'X' not found in Doppler or env`**
→ Verify `DOPPLER_TOKEN`, `DOPPLER_PROJECT`, and `DOPPLER_CONFIG` are set. Check `doppler secrets` in your CLI.

**`FastAPILimiter.init` fails on startup**
→ Redis is not reachable. Confirm `REDIS_HOST` is correct and the Redis server is running.

**`VectorStore.__init__` error**
→ Confirm `QDRANT_URL` and `QDRANT_API_KEY` are valid. Check Qdrant Cloud cluster status.

**`VerifyMismatchError` on login**
→ Expected — wrong password. Not a bug.

**Chat returns "Try again later!"**
→ Check `app.log` for the full traceback. Common causes: Gemini API quota exceeded, Qdrant unreachable, or empty document corpus for the user.

**Document upload shows `"Embedding failed"` in `failed` array**
→ The file parsed successfully but vector upsert failed. Check Qdrant connectivity and the embedding size matches `VECTOR_SIZE = 3072`.

**Rate limit `429` on `/chat`**
→ More than 10 requests within 60 seconds from this token. Wait for the window to reset.

---

## Developer Notes

- **Module entry points.** `SQL_Database.py`, `Vector_Store.py`, and `EmbeddingsGenerationnStorage.py` each contain `if __name__ == "__main__"` blocks for direct testing. Run them as `python -m DATABASE.SQL_Database`, etc.
- **Qdrant payload index is idempotent.** `create_payload_index` is called on every startup but is safe to call multiple times.
- **`lru_cache` and multi-process deployments.** `load_env_from_secret` is cached per process. With multiple Gunicorn workers, Doppler is called once per worker at startup — this is expected and acceptable.
- **Temp file cleanup.** The `addDocument` handler has both a `finally` block inside the per-file loop and a top-level `finally` for the last `temp_path`. This is belt-and-suspenders to handle edge cases where an exception escapes the inner loop.
- **Chat history concurrency.** Redis list operations (`RPUSH` + `LTRIM`) are pipelined in a single transaction, making concurrent turn insertions safe under high load.

---

## Production Recommendations

1. **Enable Redis AOF persistence** (`appendonly yes`) to prevent token blacklist loss on restart.
2. **Set `PYTHONUNBUFFERED=1`** in your container so logs stream immediately.
3. **Configure Qdrant HNSW parameters** (`m`, `ef_construct`) based on expected collection size — defaults are appropriate up to ~1M vectors.
4. **Rotate JWT secrets periodically** — implement a key ID (`kid`) header and dual-key validation window to allow zero-downtime rotation.
5. **Monitor Gemini quota** — the pipeline makes 3–5 Gemini calls per chat turn (condensation, sub-queries, N×HyDE, synthesis). Plan token budgets accordingly.
6. **Add CORS middleware** if this API will be consumed by a separate frontend origin.
7. **Log aggregation** — ship `app.log` to a centralised system (Datadog, Loki, CloudWatch) for production observability.

---

## License

MIT — see [LICENSE](LICENSE) for full terms.

---

## Credits

Built with [FastAPI](https://fastapi.tiangolo.com), [Qdrant](https://qdrant.tech), [Google Gemini](https://ai.google.dev), [SQLAlchemy](https://sqlalchemy.org), and [Redis](https://redis.io).

Secret management powered by [Doppler](https://doppler.com).
