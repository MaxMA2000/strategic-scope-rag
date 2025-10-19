from typing import Dict, Any
from core import logger
from graph.state import RAGState


async def retrieve_dense(state: RAGState, index_service) -> Dict[str, Any]:
    """Retrieve from Qdrant (dense vectors)."""
    try:
        logger.info(f"Dense retrieval for project {state['project_id']}")
        
        from core.settings import settings
        
        result = await index_service.search(
            state["project_id"],
            state["message"],
            k=settings.retrieval_top_k_dense
        )
        
        dense_candidates = [
            {
                "text": r.text,
                "score": r.score,
                "metadata": r.metadata,
                "source": "dense"
            }
            for r in result.results
        ]
        
        logger.info(f"Dense retrieval: {len(dense_candidates)} candidates")
        return {"dense_candidates": dense_candidates}
    
    except Exception as e:
        logger.error(f"Dense retrieval failed: {e}", exc_info=True)
        return {"dense_candidates": [], "errors": state.get("errors", []) + [str(e)]}


async def retrieve_sparse(state: RAGState, index_service) -> Dict[str, Any]:
    """Retrieve from Meilisearch (sparse BM25)."""
    try:
        logger.info(f"Sparse retrieval for project {state['project_id']}")
        
        from core.settings import settings
        
        result = await index_service.search(
            state["project_id"],
            state["message"],
            k=settings.retrieval_top_k_sparse
        )
        
        sparse_candidates = [
            {
                "text": r.text,
                "score": r.score,
                "metadata": r.metadata,
                "source": "sparse"
            }
            for r in result.results
        ]
        
        logger.info(f"Sparse retrieval: {len(sparse_candidates)} candidates")
        return {"sparse_candidates": sparse_candidates}
    
    except Exception as e:
        logger.error(f"Sparse retrieval failed: {e}", exc_info=True)
        return {"sparse_candidates": [], "errors": state.get("errors", []) + [str(e)]}

