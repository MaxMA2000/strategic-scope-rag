from typing import List, Dict, Any, Optional, TypedDict, Literal


class RAGState(TypedDict, total=False):
    """State for RAG graph."""
    
    # Input
    project_id: str
    session_id: str
    message: str
    mode: Optional[Literal["brief", "swot", "sizing", "issue_tree", "risks", "action_plan"]]
    
    # Retrieval
    dense_candidates: List[Dict[str, Any]]
    sparse_candidates: List[Dict[str, Any]]
    fused_candidates: List[Dict[str, Any]]
    
    # Grading & reranking
    relevance_grade: str  # "yes" | "no"
    reranked_candidates: List[Dict[str, Any]]
    
    # Context
    context: str
    citations: List[Dict[str, Any]]
    
    # Generation
    tokens: List[str]
    used_retrieval: bool
    
    # Errors
    errors: List[str]

