from fastapi import FastAPI, UploadFile, File, Query, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import uuid
import time

from core import settings, logger
from core.models import (
    ProjectCreate, Project, ParseRequest, ParseResponse,
    CrawlStartRequest, CrawlStatusResponse,
    IndexBuildRequest, IndexBuildResponse,
    SearchRequest, SearchResponse,
    ChatRequest, ChatClearRequest,
    ExportBriefingRequest,
    DocumentUploadResponse
)

# Import services (will be implemented)
from services.project_service import ProjectService
from services.pdf_service import PDFService
from services.crawl_service import CrawlService
from services.index_service import IndexService

# Import graph
from graph.graph import RAGGraphWrapper


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler for startup/shutdown."""
    logger.info("Starting Strategic Scope RAG API...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"LangSmith tracing: {settings.langchain_tracing_v2}")
    
    # Initialize services
    app.state.project_service = ProjectService()
    app.state.pdf_service = PDFService()
    app.state.crawl_service = CrawlService()
    app.state.index_service = IndexService()
    app.state.rag_graph = RAGGraphWrapper()
    
    logger.info("Services initialized successfully")
    
    yield
    
    logger.info("Shutting down Strategic Scope RAG API...")


app = FastAPI(
    title="Strategic Scope RAG API",
    description="Production-grade RAG system for technology/strategy consulting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_id(prefix: str = "id") -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def error_response(code: str, message: str, status_code: int = 400) -> JSONResponse:
    """Standard error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message},
            "request_id": generate_id("req"),
            "timestamp": int(time.time())
        }
    )


# ============================================================================
# HEALTH & METRICS
# ============================================================================

@app.get(f"{settings.api_prefix}/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env
    }


@app.get(f"{settings.api_prefix}/metrics", tags=["Health"])
async def metrics():
    """Basic metrics endpoint (Prometheus format optional)."""
    return {
        "status": "ok",
        "message": "Metrics endpoint - Prometheus integration TBD"
    }


# ============================================================================
# PROJECTS
# ============================================================================

@app.post(f"{settings.api_prefix}/projects", tags=["Projects"], response_model=Project)
async def create_project(req: ProjectCreate):
    """Create a new project."""
    try:
        project = await app.state.project_service.create_project(req.name, req.description)
        return project
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.api_prefix}/projects", tags=["Projects"], response_model=list[Project])
async def list_projects():
    """List all projects."""
    try:
        projects = await app.state.project_service.list_projects()
        return projects
    except Exception as e:
        logger.error(f"Failed to list projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.api_prefix}/projects/{{project_id}}", tags=["Projects"], response_model=Project)
async def get_project(project_id: str):
    """Get project by ID."""
    try:
        project = await app.state.project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DOCUMENTS
# ============================================================================

@app.post(f"{settings.api_prefix}/documents/upload", tags=["Documents"], response_model=DocumentUploadResponse)
async def upload_document(
    project_id: str = Query(...),
    file: UploadFile = File(...)
):
    """Upload a document (PDF/PPTX/DOCX)."""
    try:
        content = await file.read()
        result = await app.state.pdf_service.save_upload(
            project_id=project_id,
            filename=file.filename,
            content=content
        )
        return result
    except Exception as e:
        logger.error(f"Failed to upload document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.api_prefix}/documents", tags=["Documents"])
async def list_documents(project_id: str = Query(...)):
    """List documents for a project."""
    try:
        docs = await app.state.pdf_service.list_documents(project_id)
        return {"documents": docs}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.api_prefix}/parse", tags=["Documents"], response_model=ParseResponse)
async def parse_document(req: ParseRequest, background_tasks: BackgroundTasks):
    """Trigger document parsing in background."""
    try:
        job_id = generate_id("job")
        background_tasks.add_task(
            app.state.pdf_service.parse_document,
            req.project_id,
            req.document_id,
            job_id
        )
        return ParseResponse(job_id=job_id, status="accepted")
    except Exception as e:
        logger.error(f"Failed to start parse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRAWL
# ============================================================================

@app.post(f"{settings.api_prefix}/crawl/start", tags=["Crawl"])
async def start_crawl(req: CrawlStartRequest, background_tasks: BackgroundTasks):
    """Start web crawling job."""
    try:
        job_id = generate_id("crawl")
        background_tasks.add_task(
            app.state.crawl_service.run_crawl,
            job_id,
            req.project_id,
            req.seed_urls,
            req.max_depth,
            req.max_pages,
            req.allow_render,
            req.include_patterns,
            req.exclude_patterns
        )
        return {"job_id": job_id, "status": "started"}
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.api_prefix}/crawl/status", tags=["Crawl"], response_model=CrawlStatusResponse)
async def crawl_status(job_id: str = Query(...)):
    """Get crawl job status."""
    try:
        status = await app.state.crawl_service.get_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crawl status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INDEX
# ============================================================================

@app.post(f"{settings.api_prefix}/index/build", tags=["Index"], response_model=IndexBuildResponse)
async def build_index(req: IndexBuildRequest):
    """Build hybrid index (Qdrant + Meilisearch)."""
    try:
        result = await app.state.index_service.build_index(
            req.project_id,
            req.force_rebuild
        )
        return result
    except Exception as e:
        logger.error(f"Failed to build index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.api_prefix}/index/search", tags=["Index"], response_model=SearchResponse)
async def search_index(req: SearchRequest):
    """Search hybrid index."""
    try:
        result = await app.state.index_service.search(
            req.project_id,
            req.query,
            req.k
        )
        return result
    except Exception as e:
        logger.error(f"Failed to search index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT (SSE)
# ============================================================================

@app.post(f"{settings.api_prefix}/chat", tags=["Chat"])
async def chat(req: ChatRequest):
    """RAG chat with streaming (SSE)."""
    
    async def event_generator():
        try:
            # Invoke LangGraph streaming
            async for event in app.state.rag_graph.astream({
                "project_id": req.project_id,
                "session_id": req.session_id or "default",
                "message": req.message,
                "mode": req.mode
            }):
                # Forward graph events as SSE
                if "citations" in event:
                    for citation in event["citations"]:
                        yield f"event: citation\n"
                        yield f"data: {citation}\n\n"
                
                if "token" in event:
                    yield f"event: token\n"
                    yield f'data: {{"text": "{event["token"]}"}}\n\n'
                
                if "done" in event:
                    yield f"event: done\n"
                    yield f'data: {{"used_retrieval": {str(event.get("used_retrieval", False)).lower()}}}\n\n'
        
        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f"event: error\n"
            yield f'data: {{"message": "Internal error"}}\n\n'
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post(f"{settings.api_prefix}/chat/clear", tags=["Chat"])
async def clear_chat(req: ChatClearRequest):
    """Clear chat session history."""
    try:
        # Clear from Redis via service
        session_id = req.session_id or "default"
        # TODO: implement clear_session in a session service
        return {"ok": True, "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to clear chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT
# ============================================================================

@app.post(f"{settings.api_prefix}/export/briefing", tags=["Export"])
async def export_briefing(req: ExportBriefingRequest):
    """Export consulting briefing as Markdown."""
    try:
        # TODO: implement export logic
        return {
            "ok": True,
            "template": req.template,
            "message": "Export feature coming in P1"
        }
    except Exception as e:
        logger.error(f"Failed to export briefing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

