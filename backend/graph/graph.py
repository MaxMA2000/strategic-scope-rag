from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableParallel

from graph.state import RAGState
from graph.nodes.retrieve import retrieve_dense, retrieve_sparse
from graph.nodes.fuse import fuse_results
from graph.nodes.grade import grade_relevance
from graph.nodes.rerank import rerank_candidates
from graph.nodes.build_context import build_context
from graph.nodes.generate import generate_answer

from core import logger


def create_rag_graph():
    """Create the RAG graph with all nodes and edges."""
    
    # Define graph
    workflow = StateGraph(RAGState)
    
    # We'll use a functional approach since LangGraph doesn't allow direct
    # dependency injection in node functions. We'll create wrapper nodes.
    
    # For MVP, we'll use a simpler approach: single retrieval → grade → rerank → generate
    # Dense + Sparse parallel retrieval is complex in LangGraph, so we'll do sequential for now
    
    def retrieve_node(state: RAGState):
        """Combined retrieval node."""
        # This would call both retrieve_dense and retrieve_sparse
        # For now, simplified
        from services.index_service import IndexService
        import asyncio
        
        index_service = IndexService()
        
        # Run both in parallel
        dense_task = retrieve_dense(state, index_service)
        sparse_task = retrieve_sparse(state, index_service)
        
        dense_result = asyncio.run(dense_task)
        sparse_result = asyncio.run(sparse_task)
        
        return {**dense_result, **sparse_result}
    
    def fuse_node(state: RAGState):
        return fuse_results(state)
    
    def grade_node(state: RAGState):
        import asyncio
        return asyncio.run(grade_relevance(state))
    
    def rerank_node(state: RAGState):
        import asyncio
        return asyncio.run(rerank_candidates(state))
    
    def context_node(state: RAGState):
        return build_context(state)
    
    async def generate_node(state: RAGState):
        """Generate node that yields events."""
        async for event in generate_answer(state):
            yield event
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("fuse", fuse_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("context", context_node)
    workflow.add_node("generate", generate_node)
    
    # Add edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "fuse")
    workflow.add_edge("fuse", "grade")
    
    # Conditional edge from grade
    def should_use_context(state: RAGState) -> Literal["rerank", "generate"]:
        grade = state.get("relevance_grade", "no")
        return "rerank" if grade == "yes" else "generate"
    
    workflow.add_conditional_edges(
        "grade",
        should_use_context,
        {
            "rerank": "rerank",
            "generate": "generate"
        }
    )
    
    workflow.add_edge("rerank", "context")
    workflow.add_edge("context", "generate")
    workflow.add_edge("generate", END)
    
    # Compile
    app = workflow.compile()
    
    logger.info("RAG graph compiled successfully")
    return app


# Simplified streaming wrapper
class RAGGraphWrapper:
    """Wrapper to provide streaming interface."""
    
    def __init__(self):
        from services.index_service import IndexService
        self.index_service = IndexService()
    
    async def astream(self, inputs: dict):
        """Stream RAG execution."""
        try:
            # Manual execution for MVP (LangGraph streaming is complex)
            state = RAGState(**inputs)
            
            # Retrieve
            from graph.nodes.retrieve import retrieve_dense, retrieve_sparse
            dense_result = await retrieve_dense(state, self.index_service)
            sparse_result = await retrieve_sparse(state, self.index_service)
            state.update(dense_result)
            state.update(sparse_result)
            
            # Fuse
            from graph.nodes.fuse import fuse_results
            fused = fuse_results(state)
            state.update(fused)
            
            # Grade
            from graph.nodes.grade import grade_relevance
            grade_result = await grade_relevance(state)
            state.update(grade_result)
            
            # Rerank if relevant
            if state.get("relevance_grade") == "yes":
                from graph.nodes.rerank import rerank_candidates
                rerank_result = await rerank_candidates(state)
                state.update(rerank_result)
                
                # Build context
                from graph.nodes.build_context import build_context
                context_result = build_context(state)
                state.update(context_result)
            else:
                state["context"] = ""
                state["citations"] = []
                state["used_retrieval"] = False
            
            # Generate
            from graph.nodes.generate import generate_answer
            async for event in generate_answer(state):
                yield event
        
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            yield {"error": str(e)}

