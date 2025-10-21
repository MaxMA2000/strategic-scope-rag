# Strategic Scope RAG

A production-grade RAG (Retrieval-Augmented Generation) system designed for technology and strategy consultants. Built with LangGraph, Azure OpenAI, and hybrid retrieval (Qdrant + Meilisearch).

## Features

- **Multi-source ingestion**: Upload PDFs/PPTX/DOCX and crawl public websites
- **Hybrid retrieval**: Dense vectors (Qdrant) + Sparse BM25 (Meilisearch) with reciprocal rank fusion
- **LLM reranking**: GPT-4o-mini for precision relevance grading and reranking
- **Streaming chat**: SSE-based chat with real-time citations
- **Consulting templates**: Executive briefs, SWOT analysis, market sizing, issue trees, risk assessments
- **Observable**: LangSmith tracing, structured logging, Prometheus metrics
- **Docker-ready**: Complete docker-compose setup for local development

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  LangGraph   │────▶│ Azure GPT   │
│     API     │     │     Graph    │     │  4o/4o-mini │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│   Qdrant    │     │ Meilisearch  │
│  (Dense)    │     │   (BM25)     │
└─────────────┘     └──────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)
- Azure OpenAI account with GPT-4o and embedding deployments

### 1. Clone and Configure

```bash
git clone <repo-url>
cd strategic-scope-rag

# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env with your Azure OpenAI credentials
```

### 2. Start Services

```bash
# Start all services (Qdrant, Meilisearch, Redis, API, Web)
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### 3. Verify

- API: http://localhost:8001/api/v1/health
- API Docs: http://localhost:8001/docs
- Frontend: http://localhost:3000 (when implemented)
- Qdrant: http://localhost:6333/dashboard
- Meilisearch: http://localhost:7700

## Development Setup (Local)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
# source venv/bin/activate  # Windows: venv\Scripts\activate
source activate strategic-scope-rag

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Start services (Redis, Qdrant, Meilisearch)
docker compose up redis qdrant meilisearch -d

# Run API
uvicorn app:app --reload --port 8001
```

### Frontend

```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Usage

### 1. Create a Project

```bash
curl -X POST http://localhost:8001/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Trends 2025", "description": "Analysis of emerging tech trends"}'
```

### 2. Upload Documents

```bash
curl -X POST "http://localhost:8001/api/v1/documents/upload?project_id=proj_xxx" \
  -F "file=@/path/to/document.pdf"
```

### 3. Parse Document

```bash
curl -X POST http://localhost:8001/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_xxx", "document_id": "doc_yyy"}'
```

### 4. Build Index

```bash
curl -X POST http://localhost:8001/api/v1/index/build \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_xxx"}'
```

### 5. Chat with RAG

```bash
# SSE stream
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_xxx",
    "message": "What are the top 5 technology trends for 2025?",
    "mode": "brief"
  }'
```

### 6. Start Web Crawl

```bash
curl -X POST http://localhost:8001/api/v1/crawl/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_xxx",
    "seed_urls": ["https://example.com/tech-trends"],
    "max_depth": 2,
    "max_pages": 50
  }'
```

## API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents` - List documents
- `POST /api/v1/parse` - Parse document

### Crawl
- `POST /api/v1/crawl/start` - Start crawl job
- `GET /api/v1/crawl/status` - Get crawl status

### Index
- `POST /api/v1/index/build` - Build hybrid index
- `POST /api/v1/index/search` - Search index

### Chat
- `POST /api/v1/chat` - RAG chat (SSE)
- `POST /api/v1/chat/clear` - Clear session

### Export
- `POST /api/v1/export/briefing` - Export briefing

## Configuration

Key environment variables in `backend/.env`:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-3-small

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key

# Retrieval tuning
RETRIEVAL_TOP_K_DENSE=50
RETRIEVAL_TOP_K_SPARSE=50
RETRIEVAL_FUSION_TOP_N=30
RETRIEVAL_RERANK_TOP_K=8
```

## Project Structure

```
strategic-scope-rag/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── core/
│   │   ├── settings.py           # Configuration
│   │   ├── logging.py            # Structured logging
│   │   └── models.py             # Pydantic models
│   ├── services/
│   │   ├── project_service.py    # Project management
│   │   ├── pdf_service.py        # Document parsing
│   │   ├── crawl_service.py      # Web crawler
│   │   └── index_service.py      # Hybrid indexing
│   ├── graph/
│   │   ├── state.py              # LangGraph state
│   │   ├── graph.py              # Graph definition
│   │   └── nodes/                # Graph nodes
│   │       ├── retrieve.py       # Dense + Sparse retrieval
│   │       ├── fuse.py           # Reciprocal rank fusion
│   │       ├── grade.py          # Relevance grading
│   │       ├── rerank.py         # LLM reranking
│   │       ├── build_context.py  # Context building
│   │       └── generate.py       # Streaming generation
│   ├── requirements.txt
│   └── Dockerfile
├── web/                          # Next.js frontend (TBD)
├── data/                         # Runtime data (gitignored)
├── compose.yaml                  # Docker compose
└── README.md
```

## Performance Targets

- **Time to First Token (TTFT)**: < 1.2s (p50)
- **Total Latency**: < 4s (p50)
- **Retrieval Precision**: > 60% used_retrieval rate
- **Crawl Speed**: 200 pages in < 5 minutes
- **Index Build**: < 2 minutes for 1000 chunks

## LangSmith Integration

If you have LangSmith enabled, all graph executions are traced:

1. Visit https://smith.langchain.com
2. Select project: `strategic-scope-rag`
3. View traces for each chat interaction
4. Analyze retrieval quality, latency, token usage

## Troubleshooting

### Services won't start
```bash
# Check Docker
docker-compose ps

# View logs
docker-compose logs api

# Restart services
docker-compose restart
```

### Parsing fails
- Check if Unstructured dependencies are installed
- For OCR: ensure PaddleOCR is installed (optional)
- Check document format is supported (PDF, PPTX, DOCX)

### No retrieval results
- Verify index is built: `POST /api/v1/index/build`
- Check Qdrant collection exists: http://localhost:6333/dashboard
- Verify Meilisearch index: http://localhost:7700

### Slow responses
- Check Azure OpenAI quota/rate limits
- Monitor Redis cache hit rate
- Review LangSmith traces for bottlenecks

## Roadmap

### Phase 0 (MVP) ✅
- [x] Document upload and parsing
- [x] Hybrid retrieval (Qdrant + Meilisearch)
- [x] LangGraph orchestration
- [x] Streaming chat with citations
- [x] Docker compose setup

### Phase 1 (Current)
- [ ] Web crawler implementation
- [ ] Frontend UI (Next.js)
- [ ] Document viewer with overlays
- [ ] Consulting prompt templates
- [ ] Markdown export

### Phase 2 (Future)
- [ ] Redis caching for embeddings
- [ ] Session history persistence
- [ ] Multi-document comparison ("what changed?")
- [ ] Table extraction to CSV
- [ ] Grafana dashboards
- [ ] LangSmith evaluation datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: <repo-url>/issues
- Documentation: <repo-url>/wiki
