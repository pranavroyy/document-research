# AI Research Paper Assistant

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![License](https://img.shields.io/badge/License-MIT-green)

Upload research-paper PDFs and ask questions about them. Answers stream live and come with the pages they were drawn from. Everything runs locally: embeddings and reranking via Sentence Transformers, the LLM via Ollama, storage in PostgreSQL + pgvector.

The core idea: **not every question is a vector-search question.** A router sends each query down the pipeline that fits it.

| You ask | Route | What happens |
|---|---|---|
| "Who are the authors?" / "How many pages?" | `metadata` | Answered from structured fields. No retrieval, no generation. |
| "Summarize this paper." | `synthesis` | LLM over the stored title, authors and abstract. |
| "Compare these two papers." | `comparison` | Top chunks retrieved per document so each paper gets equal evidence. |
| "What accuracy did DBSCAN achieve?" | `rag` | Hybrid retrieval, cross-encoder rerank, grounded generation. |

---

## Screenshots

| Home | Streaming answer |
|---|---|
| ![Home](docs/home.png) | ![Streaming Answer](docs/streaming-answer.png) |

| Sources with page numbers | Evaluation run |
|---|---|
| ![Sources](docs/sources.png) | ![Evaluation](docs/eval-output.png) |

---

## Architecture

```mermaid
flowchart TD
    UI[React + TypeScript UI] -->|POST /chat/stream · SSE| API[FastAPI]
    API --> R{Intent router}
    R -->|metadata| M[Metadata lookup]
    R -->|synthesis| S[Synthesis]
    R -->|comparison| C[Per-document retrieval]
    R -->|rag| H[Hybrid retrieval]
    H --> D[(pgvector cosine search)]
    H --> F[(Postgres full-text search)]
    D --> X[Cross-encoder rerank]
    F --> X
    X --> L[Ollama · Llama 3.2 3B]
    S --> L
    C --> L
    L --> UI
```

### Ingestion

```
PDF upload
  → Docling: markdown + page count
  → LLM metadata extraction (title, authors, abstract) from the first 4,000 characters
  → pypdf: per-page text (keeps page numbers for sources)
  → clean + RecursiveCharacterTextSplitter (1000 chars, 200 overlap, chunks < 80 chars dropped)
  → all-MiniLM-L6-v2 embeddings (384-dim)
  → PostgreSQL: documents + chunks(embedding vector(384), page_number)
```

### Query flow (`rag` route)

1. **Route.** Deterministic rules first (very short queries go to RAG, "page" questions go to metadata). Otherwise Llama 3.2 classifies the query as JSON, validated with Pydantic. Any parse or validation failure falls back to `rag`.
2. **Retrieve.** Two candidate lists of `max(top_k × 4, 20)` chunks each: pgvector cosine distance, and Postgres full-text search (`to_tsvector` / `plainto_tsquery` / `ts_rank`). Both honour the selected-document filter.
3. **Merge and rerank.** Candidates are de-duplicated by chunk id, then scored as (question, chunk) pairs by `cross-encoder/ms-marco-MiniLM-L-6-v2`. The top `k` are kept.
4. **Generate.** The chunks go into a prompt that says to answer only from the context and to say so when the context is insufficient (temperature 0.2).
5. **Stream.** Server-Sent Events: `intent`, `retrieval`, many `token`, `sources`, `done`.

---

## Design notes

- **Why a router?** Metadata questions have exact answers in structured fields, so retrieval would only add latency and hallucination risk. Summaries need global context, not the top few chunks.
- **Why hybrid retrieval?** Dense search handles paraphrase. Keyword search catches acronyms, numbers and rare names ("IFAT", "89.6") that embeddings blur.
- **Why a cross-encoder?** Bi-encoders embed query and chunk separately, which is fast but coarse. A cross-encoder reads them together, which is slower but more precise, so it only runs on the ~20–40 candidates.
- **Why pgvector?** One database for documents, metadata and vectors, with SQL filters and transactional consistency. A dedicated vector store only pays off at far larger scale.
- **Why SSE?** Token streaming is one-way, so plain HTTP with `text/event-stream` is simpler than WebSockets.
- **Layering:** `api` (HTTP) → `services` (business and AI logic) → `repositories` (queries) with `schemas` (Pydantic) and `models` (SQLAlchemy).

---

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Axios |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Retrieval | pgvector, PostgreSQL full-text search, Sentence Transformers (`all-MiniLM-L6-v2`), CrossEncoder (`ms-marco-MiniLM-L-6-v2`) |
| Parsing | Docling, pypdf, LangChain text splitters |
| LLM | Ollama, Llama 3.2 3B (default) |
| Infra | Docker Compose, GitHub Actions (import check, pytest, frontend build) |

---

## Getting started

### Prerequisites
Docker with Compose, [Ollama](https://ollama.com/download), Node.js 20+ (only for running the frontend outside Docker).

### 1. Clone and configure
```bash
git clone https://github.com/pranavroyy/document-research.git
cd document-research
cp .env.example .env
```

### 2. Start Ollama and pull the model
```bash
ollama serve
ollama pull llama3.2:3b
```
The backend container reaches Ollama on your host at `http://host.docker.internal:11434` (set in `docker-compose.yml`). On Linux you may need to add `extra_hosts: ["host.docker.internal:host-gateway"]` to the backend service.

### 3. Start the stack
```bash
docker compose up --build
```

### 4. Run migrations
```bash
docker compose exec backend alembic upgrade head
```
The first migration enables the `vector` extension and creates the base tables; later ones add metadata and page numbers.

### 5. Use it
- UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Upload one or more PDFs, wait for indexing, optionally select specific documents, then ask. The first upload is slow because the embedding and reranker models are downloaded and loaded.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ai_research` | Postgres connection |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model for routing, metadata, generation |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |

### Run without Docker
```bash
# backend
cd backend && pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Parse, extract metadata, chunk, embed and index a PDF |
| `GET` | `/documents` | List indexed documents |
| `POST` | `/search` | Dense semantic search over chunks |
| `POST` | `/chat` | Routed question, full JSON response |
| `POST` | `/chat/stream` | Routed question, streamed over SSE |
| `GET` | `/health` | Liveness check |

Chat request body: `{"question": "...", "top_k": 5, "document_ids": [1, 2]}` (`document_ids` optional).

Example SSE stream for a `rag` question:
```
event: intent      data: {"route": "rag", ...}
event: retrieval   data: {"mode": "hybrid", "reranking": true, "top_k": 5}
event: token       data: "DBSCAN reached ..."
event: sources     data: [{"filename": "paper.pdf", "page_number": 7, ...}]
event: done        data: {"done": true}
```
Only the `rag` route streams token by token. Other routes send the full answer as a single `token` event.

---

## Evaluation

`backend/evals/run_eval.py` runs benchmark questions (`questions.json`) through the hybrid retriever and checks whether the top-5 chunks contain the expected evidence keywords. A question passes at ≥ 70% keyword coverage.

```bash
docker compose exec backend python -m evals.run_eval
```

This is a smoke test and regression guard, not a full retrieval benchmark: it is keyword-based, the question set is small and drawn from one paper, and it does not compare retrieval modes. Rank-aware metrics (Recall@K, MRR, nDCG) are on the roadmap.

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```
Current tests cover cleaning and chunking. CI runs on every push and PR to `main`.

---

## Known limitations

- **PDF only.** No DOCX or other formats; OCR and table-structure extraction are disabled in the Docling pipeline, so scanned PDFs and tables are weak.
- **Keyword leg is not BM25.** It uses Postgres `ts_rank` (no corpus-level IDF), and `plainto_tsquery` requires every query word to match, so long natural-language questions can return no keyword hits. The dense leg and reranker carry those queries.
- **No ANN index.** Vector and full-text searches are sequential scans. Fine for hundreds of papers; add HNSW and a GIN `tsvector` index for scale.
- **Naive merge.** Candidates are unioned, not score-fused (no RRF).
- **Summaries use metadata only.** The `synthesis` route summarizes the stored abstract, not the full paper. The `comparison` route uses dense retrieval only (no rerank).
- **Router edge cases.** Any question containing "page" is routed to page count.
- **Sources, not inline citations.** The UI lists the retrieved chunks; the answer itself does not cite them.
- **Synchronous ingestion**, one-by-one embedding, no auth, no conversation memory.
- **Context window.** Set Ollama's `num_ctx` if you raise `top_k` so prompts aren't truncated silently. MiniLM also truncates text beyond ~256 tokens when embedding.

---

## Roadmap

- [x] React UI, FastAPI backend, Docker Compose
- [x] pgvector storage, Docling parsing, LLM metadata extraction
- [x] Intent routing, multi-document queries
- [x] Hybrid retrieval, cross-encoder reranking, page-aware sources
- [x] SSE streaming, keyword-coverage eval, GitHub Actions CI
- [ ] Labelled retrieval benchmark: Recall@K, MRR, nDCG for dense / FTS / hybrid / hybrid + rerank
- [ ] `websearch_to_tsquery` or true BM25, RRF fusion
- [ ] HNSW + GIN indexes
- [ ] DOCX support, OCR and tables
- [ ] Full-document (map-reduce) summarization
- [ ] Background ingestion jobs, batch embedding
- [ ] Conversation history with query rewriting
- [ ] Faithfulness evaluation (RAGAS / LLM-as-judge)
- [ ] Authentication

---

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under the MIT License, see [LICENSE](LICENSE).
