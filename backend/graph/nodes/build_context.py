from typing import Dict, Any
from graph.state import RAGState
from core import logger


def build_context(state: RAGState) -> Dict[str, Any]:
    """Build context and citations from reranked candidates."""
    reranked = state.get("reranked_candidates", [])
    
    if not reranked:
        return {"context": "", "citations": [], "used_retrieval": False}
    
    # Build context text
    context_parts = []
    citations = []
    
    for i, cand in enumerate(reranked, start=1):
        # Add to context
        context_parts.append(f"[{i}] {cand['text']}")
        
        # Create citation
        citation = {
            "citation_id": f"cite_{i}",
            "rank": i,
            "snippet": cand["text"][:500],
            "score": cand.get("fused_score", 0),
            "metadata": cand.get("metadata", {}),
            "document_id": cand.get("metadata", {}).get("document_id"),
            "page": cand.get("metadata", {}).get("page")
        }
        citations.append(citation)
    
    context = "\n\n".join(context_parts)
    
    logger.info(f"Built context with {len(citations)} citations ({len(context)} chars)")
    
    return {
        "context": context,
        "citations": citations,
        "used_retrieval": True
    }

