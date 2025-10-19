from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path


# Determine the backend directory (where this file is located)
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILES = [
    BACKEND_DIR / ".env.dev",
    BACKEND_DIR / ".env",
    BACKEND_DIR / ".env.local",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    # Azure OpenAI
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_embedding_deployment_name: str = "text-embedding-3-small"
    azure_openai_mini_deployment_name: str = "gpt-4o-mini"
    
    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: Optional[str] = None
    langchain_project: str = "strategic-scope-rag"
    
    # Service URLs
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    meilisearch_url: str = "http://localhost:7700"
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    data_root: str = "./data"
    
    # Retrieval
    retrieval_top_k_dense: int = 50
    retrieval_top_k_sparse: int = 50
    retrieval_fusion_top_n: int = 30
    retrieval_rerank_top_k: int = 8
    retrieval_score_threshold: float = 0.45
    
    # Crawl
    crawl_max_depth: int = 3
    crawl_max_pages: int = 200
    crawl_rate_limit: float = 2.0
    crawl_user_agent: str = "StrategicScopeRAG/1.0"
    
    # Chunk settings
    chunk_size: int = 1200
    chunk_overlap: int = 200
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:8001"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

