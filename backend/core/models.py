from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DocumentSourceType(str, Enum):
    UPLOAD = "upload"
    CRAWL = "crawl"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    READY = "ready"
    ERROR = "error"


class CrawlJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Request/Response Models

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    document_count: int = 0
    chunk_count: int = 0


class DocumentUploadResponse(BaseModel):
    document_id: str
    project_id: str
    title: str
    pages: Optional[int] = None
    status: DocumentStatus


class ParseRequest(BaseModel):
    project_id: str
    document_id: str


class ParseResponse(BaseModel):
    job_id: str
    status: str


class CrawlStartRequest(BaseModel):
    project_id: str
    seed_urls: List[str] = Field(..., min_items=1)
    max_depth: int = Field(default=2, ge=1, le=5)
    max_pages: int = Field(default=100, ge=1, le=1000)
    allow_render: bool = False
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class CrawlStatusResponse(BaseModel):
    job_id: str
    status: CrawlJobStatus
    progress: float = 0.0
    pages_crawled: int = 0
    pages_total: Optional[int] = None
    error_message: Optional[str] = None


class IndexBuildRequest(BaseModel):
    project_id: str
    force_rebuild: bool = False


class IndexBuildResponse(BaseModel):
    ok: bool
    chunks: int
    reused: bool = False


class SearchRequest(BaseModel):
    project_id: str
    query: str
    k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    page: Optional[int] = None


class SearchResponse(BaseModel):
    ok: bool
    results: List[SearchResult]
    query: str


class ChatRequest(BaseModel):
    project_id: str
    message: str
    session_id: Optional[str] = None
    mode: Optional[Literal["default", "brief", "swot", "sizing", "issue_tree", "risks", "action_plan"]] = None
    use_retrieval: Optional[bool] = True
    stream: Optional[bool] = True


class ChatClearRequest(BaseModel):
    project_id: str
    session_id: Optional[str] = None


class ExportBriefingRequest(BaseModel):
    project_id: str
    session_id: str
    template: Literal["brief", "swot", "sizing", "issue_tree", "risks", "action_plan"] = "brief"


# Internal Data Models

class Chunk(BaseModel):
    id: str
    doc_id: str
    project_id: str
    text: str
    vector_id: Optional[str] = None
    sparse_id: Optional[str] = None
    page: Optional[int] = None
    heading: Optional[str] = None
    metadata: Dict[str, Any] = {}
    content_hash: Optional[str] = None


class Document(BaseModel):
    id: str
    project_id: str
    title: str
    source_type: DocumentSourceType
    path: Optional[str] = None
    url: Optional[str] = None
    status: DocumentStatus
    created_at: datetime
    pages: Optional[int] = None
    metadata: Dict[str, Any] = {}


class Citation(BaseModel):
    citation_id: str
    file_id: str
    rank: int
    page: Optional[int] = None
    snippet: str
    score: float
    preview_url: Optional[str] = None
    document_title: Optional[str] = None

