from typing import Dict, Any, AsyncGenerator
from langchain_openai import AzureChatOpenAI
from core import logger, settings
from graph.state import RAGState


SYSTEM_INSTRUCTION = """You are a strategic consulting assistant specializing in technology and business strategy.
Use the provided context to answer questions accurately and concisely.
If no relevant context is found, answer from your general knowledge and explicitly mention that."""

ANSWER_WITH_CONTEXT = """Answer the user's question using the provided context.

Question:
{question}

Context:
{context}

Write in Markdown. Be concise but complete. Use bullet points and headers where appropriate.
Do not fabricate information not present in the context."""

ANSWER_NO_CONTEXT = """No relevant course context was found for the question.
Answer from your general knowledge. Be clear and accurate.

Question:
{question}"""

# Mode-specific templates
MODE_TEMPLATES = {
    "brief": "Provide an executive brief format with: Key Findings, Implications, Recommendations.",
    "swot": "Structure your answer as a SWOT analysis: Strengths, Weaknesses, Opportunities, Threats.",
    "sizing": "Provide a market sizing framework: TAM, SAM, SOM, key assumptions.",
    "issue_tree": "Break down the problem using an issue tree structure with branches and sub-issues.",
    "risks": "Identify and categorize risks: Strategic, Operational, Financial, Technical.",
    "action_plan": "Provide an action plan with: Objectives, Key Actions, Timeline, Success Metrics."
}


async def generate_answer(state: RAGState) -> AsyncGenerator[Dict[str, Any], None]:
    """Generate streaming answer using LLM."""
    try:
        context = state.get("context", "")
        citations = state.get("citations", [])
        used_retrieval = state.get("used_retrieval", False)
        
        # Send citations first
        if citations:
            yield {"citations": citations}
        
        # Build prompt
        if context:
            prompt = ANSWER_WITH_CONTEXT.format(
                question=state["message"],
                context=context
            )
        else:
            prompt = ANSWER_NO_CONTEXT.format(question=state["message"])
        
        # Add mode-specific instructions
        mode = state.get("mode")
        if mode and mode in MODE_TEMPLATES:
            prompt += f"\n\n{MODE_TEMPLATES[mode]}"
        
        # Create LLM
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            azure_deployment=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=0.3,
            streaming=True
        )
        
        # Stream tokens
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield {"token": chunk.content}
        
        # Send done
        yield {"done": True, "used_retrieval": used_retrieval}
        
        logger.info(f"Generation complete (used_retrieval={used_retrieval})")
    
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        yield {"error": str(e)}

