from typing import Dict, Any, List
from graph.state import RAGState
from core import logger


def fuse_results(state: RAGState) -> Dict[str, Any]:
    """Reciprocal rank fusion of dense and sparse results."""
    dense = state.get("dense_candidates", [])
    sparse = state.get("sparse_candidates", [])
    
    from core.settings import settings
    
    k_param = 60
    scores = {}
    all_candidates = {}
    
    # RRF for dense
    for rank, cand in enumerate(dense, start=1):
        key = cand["text"][:100]
        if key not in scores:
            scores[key] = 0
            all_candidates[key] = cand
        scores[key] += 1.0 / (k_param + rank)
    
    # RRF for sparse
    for rank, cand in enumerate(sparse, start=1):
        key = cand["text"][:100]
        if key not in scores:
            scores[key] = 0
            all_candidates[key] = cand
        scores[key] += 1.0 / (k_param + rank)
    
    # Sort and limit
    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    fused = []
    for key in sorted_keys[:settings.retrieval_fusion_top_n]:
        cand = all_candidates[key]
        cand["fused_score"] = scores[key]
        fused.append(cand)
    
    logger.info(f"Fused {len(dense)} dense + {len(sparse)} sparse → {len(fused)} candidates")
    return {"fused_candidates": fused}

