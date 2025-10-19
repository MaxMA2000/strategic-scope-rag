from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from core import logger, settings
from graph.state import RAGState


RERANK_PROMPT = """Given a question and a list of document passages, rank them by relevance.

Question: {question}

Passages:
{passages}

Return ONLY the passage numbers in order of relevance (most relevant first), separated by commas.
Example: 3,1,5,2,4"""


async def rerank_candidates(state: RAGState) -> Dict[str, Any]:
    """Rerank candidates using LLM."""
    try:
        fused = state.get("fused_candidates", [])
        if not fused:
            return {"reranked_candidates": []}
        
        # Limit candidates for reranking (cost control)
        candidates_to_rerank = fused[:15]
        
        # Build passages text
        passages = []
        for i, cand in enumerate(candidates_to_rerank, start=1):
            text = cand["text"][:500]
            passages.append(f"{i}. {text}...")
        passages_text = "\n\n".join(passages)
        
        # Create reranker LLM
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_mini_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=0
        )
        
        # Rerank
        prompt = RERANK_PROMPT.format(question=state["message"], passages=passages_text)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        
        # Parse ranking
        try:
            ranks = [int(x.strip()) - 1 for x in response.content.split(",") if x.strip().isdigit()]
            reranked = [candidates_to_rerank[r] for r in ranks if 0 <= r < len(candidates_to_rerank)]
            
            # Add remaining candidates not in rerank
            reranked_indices = set(ranks)
            for i, cand in enumerate(candidates_to_rerank):
                if i not in reranked_indices:
                    reranked.append(cand)
        except:
            logger.warning("Failed to parse rerank response, using original order")
            reranked = candidates_to_rerank
        
        # Limit to top k
        reranked = reranked[:settings.retrieval_rerank_top_k]
        
        logger.info(f"Reranked to top {len(reranked)} candidates")
        return {"reranked_candidates": reranked}
    
    except Exception as e:
        logger.error(f"Reranking failed: {e}", exc_info=True)
        # Fallback: use fused results
        return {
            "reranked_candidates": state.get("fused_candidates", [])[:settings.retrieval_rerank_top_k],
            "errors": state.get("errors", []) + [str(e)]
        }

