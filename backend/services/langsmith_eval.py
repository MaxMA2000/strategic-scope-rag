"""
LangSmith Evaluation Service - Create and manage evaluation datasets.

This module provides functionality for:
1. Creating evaluation datasets in LangSmith
2. Running RAG evaluations
3. Computing metrics (faithfulness, answer relevance, context relevance)
"""

import os
from typing import List, Dict, Optional
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_openai import AzureChatOpenAI
from core.settings import settings

# Initialize LangSmith client
langsmith_client = Client()


class LangSmithEvaluationService:
    """Service for creating and managing LangSmith evaluation datasets."""
    
    # Default evaluation dataset name
    DEFAULT_DATASET_NAME = "strategic-scope-rag-eval"
    
    @staticmethod
    def create_consulting_dataset(
        dataset_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create a dataset with consulting-specific test cases."""
        
        dataset_name = dataset_name or LangSmithEvaluationService.DEFAULT_DATASET_NAME
        description = description or "Evaluation dataset for Strategic Scope RAG system"
        
        # Define test cases for consulting scenarios
        test_cases = [
            {
                "inputs": {
                    "question": "What are the top 5 technology trends for 2025?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["AI", "cloud", "cybersecurity", "quantum", "5G"],
                    "min_citations": 3
                }
            },
            {
                "inputs": {
                    "question": "What are the key risks associated with AI implementation in enterprises?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["data privacy", "bias", "cost", "change management"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "Provide a SWOT analysis for cloud migration",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_structure": ["strengths", "weaknesses", "opportunities", "threats"],
                    "min_citations": 4
                }
            },
            {
                "inputs": {
                    "question": "What is the market size for generative AI tools?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["TAM", "SAM", "SOM", "growth rate"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "What implementation timeline should we expect for a large-scale digital transformation?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["phases", "milestones", "months", "years"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "What are the cost considerations for implementing a RAG system?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["compute", "storage", "API", "maintenance"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "How do we measure success in a strategy consulting engagement?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["KPIs", "metrics", "ROI", "outcomes"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "What competitive advantages does Microsoft have in the cloud market?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["Azure", "enterprise", "integration", "ecosystem"],
                    "min_citations": 2
                }
            },
            {
                "inputs": {
                    "question": "Describe the action plan for launching a new AI product",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["research", "development", "testing", "launch", "marketing"],
                    "min_citations": 3
                }
            },
            {
                "inputs": {
                    "question": "What regulatory considerations should we be aware of for AI systems in healthcare?",
                    "project_id": "eval-project-1"
                },
                "outputs": {
                    "expected_topics": ["HIPAA", "FDA", "compliance", "privacy"],
                    "min_citations": 2
                }
            }
        ]
        
        try:
            # Create or get dataset
            dataset = langsmith_client.create_dataset(
                dataset_name=dataset_name,
                description=description
            )
            
            # Add examples to dataset
            for test_case in test_cases:
                langsmith_client.create_example(
                    inputs=test_case["inputs"],
                    outputs=test_case["outputs"],
                    dataset_id=dataset.id
                )
            
            print(f"✅ Created dataset '{dataset_name}' with {len(test_cases)} examples")
            return dataset.id
        
        except Exception as e:
            print(f"❌ Failed to create dataset: {e}")
            return None
    
    @staticmethod
    def faithfulness_evaluator(run, example) -> dict:
        """
        Evaluate if the answer is faithful to the retrieved context.
        Uses LLM to check if answer is grounded in citations.
        """
        try:
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                model="gpt-4o-mini",
                temperature=0
            )
            
            answer = run.outputs.get("answer", "")
            citations = run.outputs.get("citations", [])
            
            if not citations:
                return {"key": "faithfulness", "score": 0, "comment": "No citations provided"}
            
            # Concatenate citation texts
            context = "\n\n".join([c.get("text", "") for c in citations])
            
            prompt = f"""Given the following context and answer, evaluate if the answer is faithful to the context.
Score 1 if the answer is fully supported by the context.
Score 0.5 if the answer is partially supported.
Score 0 if the answer contradicts or is not supported by the context.

Context:
{context}

Answer:
{answer}

Return only the score (0, 0.5, or 1):"""
            
            response = llm.invoke(prompt)
            score = float(response.content.strip())
            
            return {
                "key": "faithfulness",
                "score": score,
                "comment": f"Answer faithfulness score: {score}"
            }
        
        except Exception as e:
            return {"key": "faithfulness", "score": 0, "comment": f"Error: {str(e)}"}
    
    @staticmethod
    def answer_relevance_evaluator(run, example) -> dict:
        """
        Evaluate if the answer is relevant to the question.
        """
        try:
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                model="gpt-4o-mini",
                temperature=0
            )
            
            question = example.inputs.get("question", "")
            answer = run.outputs.get("answer", "")
            
            prompt = f"""Evaluate if the answer is relevant to the question.
Score 1 if the answer directly addresses the question.
Score 0.5 if the answer is somewhat relevant.
Score 0 if the answer is not relevant.

Question:
{question}

Answer:
{answer}

Return only the score (0, 0.5, or 1):"""
            
            response = llm.invoke(prompt)
            score = float(response.content.strip())
            
            return {
                "key": "answer_relevance",
                "score": score,
                "comment": f"Answer relevance score: {score}"
            }
        
        except Exception as e:
            return {"key": "answer_relevance", "score": 0, "comment": f"Error: {str(e)}"}
    
    @staticmethod
    def citation_count_evaluator(run, example) -> dict:
        """
        Evaluate if the answer has sufficient citations.
        """
        try:
            citations = run.outputs.get("citations", [])
            min_citations = example.outputs.get("min_citations", 2)
            
            score = 1.0 if len(citations) >= min_citations else len(citations) / min_citations
            
            return {
                "key": "citation_count",
                "score": score,
                "comment": f"Has {len(citations)} citations (min: {min_citations})"
            }
        
        except Exception as e:
            return {"key": "citation_count", "score": 0, "comment": f"Error: {str(e)}"}
    
    @staticmethod
    def context_relevance_evaluator(run, example) -> dict:
        """
        Evaluate if the retrieved context is relevant to the question.
        """
        try:
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                model="gpt-4o-mini",
                temperature=0
            )
            
            question = example.inputs.get("question", "")
            citations = run.outputs.get("citations", [])
            
            if not citations:
                return {"key": "context_relevance", "score": 0, "comment": "No citations"}
            
            # Check each citation's relevance
            relevant_count = 0
            for citation in citations[:5]:  # Check top 5
                context = citation.get("text", "")
                
                prompt = f"""Is this context relevant to the question? Answer with 'yes' or 'no'.

Question: {question}

Context: {context}

Answer:"""
                
                response = llm.invoke(prompt)
                if "yes" in response.content.lower():
                    relevant_count += 1
            
            score = relevant_count / min(len(citations), 5)
            
            return {
                "key": "context_relevance",
                "score": score,
                "comment": f"{relevant_count}/{min(len(citations), 5)} contexts relevant"
            }
        
        except Exception as e:
            return {"key": "context_relevance", "score": 0, "comment": f"Error: {str(e)}"}
    
    @staticmethod
    def run_evaluation(
        dataset_name: str,
        experiment_name: Optional[str] = None
    ) -> Dict:
        """
        Run evaluation on a dataset.
        
        Args:
            dataset_name: Name of the LangSmith dataset
            experiment_name: Optional name for the evaluation experiment
        
        Returns:
            Dictionary with evaluation results
        """
        
        # Define evaluators
        evaluators = [
            LangSmithEvaluationService.faithfulness_evaluator,
            LangSmithEvaluationService.answer_relevance_evaluator,
            LangSmithEvaluationService.citation_count_evaluator,
            LangSmithEvaluationService.context_relevance_evaluator,
        ]
        
        # Define the RAG function to evaluate
        def rag_function(inputs: dict) -> dict:
            """Wrapper function for RAG system evaluation."""
            # In a real scenario, this would call your RAG pipeline
            # For now, return a placeholder
            return {
                "answer": "This is a test answer",
                "citations": []
            }
        
        try:
            # Run evaluation
            results = evaluate(
                rag_function,
                data=dataset_name,
                evaluators=evaluators,
                experiment_prefix=experiment_name or "rag-eval"
            )
            
            print(f"✅ Evaluation completed for dataset '{dataset_name}'")
            return results
        
        except Exception as e:
            print(f"❌ Failed to run evaluation: {e}")
            return {}


# Initialize service instance
langsmith_eval_service = LangSmithEvaluationService()


# CLI script for creating datasets
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create-dataset":
            dataset_name = sys.argv[2] if len(sys.argv) > 2 else None
            dataset_id = langsmith_eval_service.create_consulting_dataset(dataset_name)
            print(f"Dataset ID: {dataset_id}")
        
        elif command == "run-eval":
            dataset_name = sys.argv[2] if len(sys.argv) > 2 else LangSmithEvaluationService.DEFAULT_DATASET_NAME
            results = langsmith_eval_service.run_evaluation(dataset_name)
            print(f"Results: {results}")
        
        else:
            print("Unknown command. Use 'create-dataset' or 'run-eval'")
    
    else:
        print("""
LangSmith Evaluation Service

Usage:
  python langsmith_eval.py create-dataset [dataset_name]
  python langsmith_eval.py run-eval [dataset_name]

Examples:
  python langsmith_eval.py create-dataset my-eval-dataset
  python langsmith_eval.py run-eval strategic-scope-rag-eval
""")

