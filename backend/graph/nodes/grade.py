from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from core import logger, settings
from graph.state import RAGState


GRADE_PROMPT = """You are a grader assessing relevance of retrieved context to the user's question.

Context snippets:
{context}

Question: {question}

Return exactly 'yes' if the context is helpful to answer the question, otherwise 'no'."""


async def grade_relevance(state: RAGState) -> Dict[str, Any]:
    """Grade relevance of retrieved context using LLM."""
    try:
        fused = state.get("fused_candidates", [])
        if not fused:
            logger.info("No candidates to grade, routing to no-context")
            return {"relevance_grade": "no"}
        
        # Build context snippet
        snippets = []
        for i, cand in enumerate(fused[:5], start=1):
            text = cand["text"][:300]
            snippets.append(f"[{i}] {text}...")
        context_text = "\n\n".join(snippets)
        
        # Create grader LLM
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_mini_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=0
        )
        
        # Grade
        prompt = GRADE_PROMPT.format(context=context_text, question=state["message"])
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        grade = "yes" if "yes" in response.content.lower() else "no"
        
        logger.info(f"Relevance grade: {grade}")
        return {"relevance_grade": grade}
    
    except Exception as e:
        logger.error(f"Grading failed: {e}", exc_info=True)
        return {"relevance_grade": "no", "errors": state.get("errors", []) + [str(e)]}

