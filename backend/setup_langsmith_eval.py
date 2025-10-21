#!/usr/bin/env python3
"""
Setup script for LangSmith evaluation datasets.

This script creates evaluation datasets in LangSmith with pre-defined test cases
for the Strategic Scope RAG system.

Usage:
    python setup_langsmith_eval.py
"""

import os
import sys
from services.langsmith_eval import langsmith_eval_service

def main():
    print("=" * 70)
    print("Strategic Scope RAG - LangSmith Evaluation Setup")
    print("=" * 70)
    print()
    
    # Check if LangSmith is configured
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("❌ Error: LANGCHAIN_API_KEY not set")
        print("Please set your LangSmith API key:")
        print("  export LANGCHAIN_API_KEY=your_key_here")
        return 1
    
    print("✅ LangSmith API key found")
    print()
    
    # Create default dataset
    print("Creating evaluation dataset...")
    dataset_id = langsmith_eval_service.create_consulting_dataset()
    
    if dataset_id:
        print()
        print("=" * 70)
        print("✅ Setup Complete!")
        print("=" * 70)
        print()
        print(f"Dataset ID: {dataset_id}")
        print()
        print("The evaluation dataset includes test cases for:")
        print("  • Technology trends analysis")
        print("  • Risk assessment")
        print("  • SWOT analysis")
        print("  • Market sizing")
        print("  • Implementation planning")
        print("  • Cost analysis")
        print("  • KPI definition")
        print("  • Competitive analysis")
        print("  • Product launches")
        print("  • Regulatory compliance")
        print()
        print("Next steps:")
        print("1. View the dataset in LangSmith: https://smith.langchain.com")
        print("2. Run evaluations using the LangSmith UI or API")
        print("3. Integrate evaluations into your CI/CD pipeline")
        print()
        print("To run evaluations programmatically:")
        print("  python -m services.langsmith_eval run-eval")
        print()
    else:
        print()
        print("❌ Failed to create dataset")
        print("Please check your LangSmith configuration and try again")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

