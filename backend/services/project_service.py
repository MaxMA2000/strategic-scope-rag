import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import uuid

from core import settings, logger
from core.models import Project


class ProjectService:
    """Manages projects (filesystem-based for MVP)."""
    
    def __init__(self):
        self.data_root = Path(settings.data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.projects_file = self.data_root / "projects.json"
        self._ensure_projects_file()
    
    def _ensure_projects_file(self):
        """Create projects.json if it doesn't exist."""
        if not self.projects_file.exists():
            self.projects_file.write_text("[]")
    
    def _load_projects(self) -> List[dict]:
        """Load all projects from disk."""
        return json.loads(self.projects_file.read_text())
    
    def _save_projects(self, projects: List[dict]):
        """Save projects to disk."""
        self.projects_file.write_text(json.dumps(projects, indent=2))
    
    async def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create a new project."""
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        project_dir = self.data_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (project_dir / "documents").mkdir(exist_ok=True)
        (project_dir / "chunks").mkdir(exist_ok=True)
        (project_dir / "crawls").mkdir(exist_ok=True)
        
        project_data = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "document_count": 0,
            "chunk_count": 0
        }
        
        projects = self._load_projects()
        projects.append(project_data)
        self._save_projects(projects)
        
        logger.info(f"Created project: {project_id} - {name}")
        return Project(**project_data)
    
    async def list_projects(self) -> List[Project]:
        """List all projects."""
        projects = self._load_projects()
        return [Project(**p) for p in projects]
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        projects = self._load_projects()
        for p in projects:
            if p["id"] == project_id:
                return Project(**p)
        return None
    
    async def update_counts(self, project_id: str, document_count: Optional[int] = None, chunk_count: Optional[int] = None):
        """Update project counts."""
        projects = self._load_projects()
        for p in projects:
            if p["id"] == project_id:
                if document_count is not None:
                    p["document_count"] = document_count
                if chunk_count is not None:
                    p["chunk_count"] = chunk_count
                self._save_projects(projects)
                return

