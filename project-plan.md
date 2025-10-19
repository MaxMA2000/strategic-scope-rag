# Strategic Scope RAG — Local Demo (Docker-ready, Azure OpenAI, LangGraph/LangSmith)

## Goals

- Deliver a laptop demo that feels production-grade: fast, reliable, observable.
- Ingest PDFs/PPTX/Docs and crawl public sites; unify into one searchable corpus per project.
- Hybrid retrieval (dense + sparse) with LLM reranking; SSE chat with trustworthy citations.
- Ship consulting-grade workflows (briefings, SWOT, market sizing scaffolds) and exports.

## Non-goals (MVP)

- Enterprise connectors (SharePoint/Confluence); multi-tenant auth; fine-grained RBAC.

## Architecture Overview

- Orchestration: LangGraph state machine for RAG, with nodes for retrieve → grade → rerank → generate, plus error and fallback edges. LCEL for runnables and parallelism.
- API: FastAPI (HTTP + SSE) thin layer that invokes graph.run/graph.stream; background jobs in-process (Celery-like) for parse/crawl; LangServe optional wrapper for standardized deployments.
- Stores (Docker):
- Vector: Qdrant (per-project collections)
- Sparse: Meilisearch (BM25)
- Cache/State: Redis (embedding cache, chat sessions, job queues)
- Files: local `data/` (original docs, output.md, page images, crawl snapshots)
- Models: Azure OpenAI (GPT-4o/4o-mini for gen, `text-embedding-3-small` for embeddings)
- Observability: LangSmith tracing + datasets/evals; OpenTelemetry optional; Prometheus metrics if enabled.

## Tech Stack

- Python 3.10+, FastAPI, Pydantic, Uvicorn, httpx, asyncio
- LangChain core + LCEL, LangGraph (stateful orchestration), LangSmith (traces/evals), optional LangServe
- Parsing: unstructured, PyMuPDF (fitz), PaddleOCR (optional)
- Web: trafilatura, sitemap parsing; optional Playwright rendering
- Retrieval: Qdrant, Meilisearch, hybrid fusion, LLM rerank (GPT-4o-mini), FAISS fallback
- Frontend: Next.js/React (SSE), Tailwind (or Vite React minimal)
- Infra: docker-compose; Redis; Qdrant; Meilisearch; optional Prometheus/Grafana

## Data Model (high-level)

- Project {id, name, createdAt}
- Document {id, projectId, title, sourceType: [upload|crawl], path/url, status, meta}
- Chunk {id, docId, projectId, text, vectorId, sparseId, page?, heading?, scoreMeta}
- CrawlJob {id, projectId, seedUrls[], depth, include/exclude, status, stats}
- ChatSession {id, projectId, history[], lastUsedAt}

## Ingestion Pipelines

- Uploads: write original → parse to `output.md` + page PNGs + images; extract clean text, headings, page numbers, figure/table anchors; chunk by headers with recursive char split for long blocks.
- Web crawl: BFS from seeds with robots.txt respect; dedupe by URL canonical + simhash; trafilatura boilerplate removal; optional Playwright rendering per allowlist; snapshot HTML + plain text; chunk as above.
- Enrichment: language detection, source attributions, doc date, canonical URL.
- Idempotency: content hash per chunk; skip re-embedding on unchanged content.

## LangGraph RAG (state & nodes)

- State: {projectId, sessionId, message, candidates[], context, citations[], used_retrieval, errors[]}
- Nodes:
- retrieve_dense: Qdrant top-k_d
- retrieve_sparse: Meili top-k_s
- fuse: reciprocal rank fusion → top-N
- grade: LLM grader (LangSmith traced) gates to with_context vs no_context
- rerank: LLM listwise rerank (budget-capped)
- build_context: diversity + token budget
- generate: streaming via Azure GPT-4o/4o-mini
- fail/fallback: error path or no-context path
- Edges: retrieve → fuse → (grade yes → rerank → build_context → generate) | (grade no → generate without context)
- Parallelism: retrieve_dense and retrieve_sparse run in RunnableParallel; traces captured via LangSmith.

## Retrieval Pipeline (fast and precise)

1) Sparse: Meilisearch BM25 top-k_s (k_s=50)
2) Dense: Qdrant cosine top-k_d (k_d=50; Azure embeddings)
3) Fusion: reciprocal rank fusion → top 30
4) Rerank: GPT-4o-mini listwise (LangGraph node), return top 5–8
5) Context building: diversity by doc/page, anti-redundancy, target token budget
6) Guardrails: LLM grade + score heuristics → route branch

## Generation (SSE)

- Stream tokens over SSE: citation → token → done; include `used_retrieval`.
- Prompt presets for consulting (executive brief, SWOT, market sizing scaffold, issue tree, risks, action plan) as graph inputs.
- Session memory in Redis; per-project isolation.

## Performance & Cost Controls

- Embedding batch + Redis cache; httpx async to Azure; backpressure on SSE.
- Early-exit if top-1 confident; dynamic candidate caps to limit rerank cost.
- Chunk sizes tuned (header-led + 800–1200 char sub-splits) with rich metadata.
- Optional local embedding fallback (disabled by default).

## Security & Governance

- Project sandbox in `data/<projectId>/...`; strict path joins; MIME sniffing.
- Robots.txt + crawl rate limiting; per-domain concurrency caps.
- API key via `.env`; CORS limited to localhost ports.
- Redaction hooks (regex for obvious PII) before indexing.

## Observability

- LangSmith: tracing for every node; dataset-based regression evals (answer quality, groundedness); run grouping per project and build.
- Metrics: TTFT, latency, token usage, retrieval hit rates, citation CTR; optional /metrics (Prometheus) + /health.

## API Contract (outline)

- POST `/api/v1/projects` create/list; GET `/projects/:id`
- POST `/documents/upload` (multipart); GET `/documents?projectId=`
- POST `/parse` {projectId, documentId}
- POST `/crawl/start` {projectId, seeds[], depth, allowRender?}
- GET `/crawl/status?jobId=`
- POST `/index/build` {projectId}
- POST `/index/search` {projectId, query, k}
- POST `/chat` SSE {projectId, sessionId?, message, mode?} → invokes LangGraph.stream
- POST `/chat/clear` {projectId, sessionId}
- POST `/export/briefing` {projectId, query?, template}

## UI Flow (Next.js)

- Projects: create/select
- Ingest: upload files, start parse; start crawl
- Explore: document viewer with page images and overlay boxes; chunk list
- Chat: query with prompt presets; live citations panel; copy/export
- Jobs: monitor parse/crawl/index queues
- Settings: Azure keys, crawl rules, LangSmith toggles

## Repository Layout

- `backend/`
- `app.py` (FastAPI routes, SSE → graph.stream)
- `graph/` {`state.py`, `nodes/`(`retrieve_dense.py`, `retrieve_sparse.py`, `fuse.py`, `grade.py`, `rerank.py`, `build_context.py`, `generate.py`), `graph.py`}
- `services/` {`pdf_service.py`, `crawl_service.py`, `index_service.py`}
- `core/` {`settings.py`, `logging.py`}
- `data/` (runtime artifacts)
- `web/` (Next.js)
- `docker/` (compose, service Dockerfiles)
- `compose.yaml` (api, web, qdrant, meili, redis[, grafana, prometheus])

## Docker Compose (ports)

- api:8001, web:3000, qdrant:6333, meilisearch:7700, redis:6379

## Phased Roadmap & Acceptance

- P0 (Week 1): Upload→Parse→Index→Hybrid retrieve (Qdrant+Meili)→LangGraph SSE Chat with citations; compose up. KPI: TTFT < 1.2s (p50), answer latency < 4s (p50), used_retrieval > 60%.
- P1 (Week 2): Web crawler + scheduler; doc viewer overlays; prompt presets; LangSmith baseline eval set; export Markdown. KPI: crawl 200 pages < 5 min; index rebuild < 2 min.
- P2 (Week 3): Rerank optimization; delta (“what changed?”) across docs; table extraction to CSV; Grafana dashboards; nightly LangSmith evals. KPI: top-3 precision@k +10% vs P0.

## Demo Script (10 minutes)

1) Create project; upload McKinsey PDF; parse; view page overlays
2) Crawl 1–2 competitor sites (depth 1); build index
3) Ask: “Top 5 2025 trends and enterprise implications?” → citations
4) Ask: “What changed vs 2024?” → delta across docs
5) Export “Executive Brief” → Markdown; show sources list