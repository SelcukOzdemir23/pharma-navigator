#!/usr/bin/env python3
"""
Direct test of Pharma Navigator RAG system without the Chainlit UI.
This tests the backend components directly.
"""

import asyncio
import os
import sys
sys.path.insert(0, '/media/depo/Dosya/Kodlar/pharma-navigator')

from src.models.intent import classify_intent
from src.models.qa import generate_answer
from src.retrieval.retriever import DrugRetriever
import dspy
import tomli

# Load config
def load_config():
    with open('/media/depo/Dosya/Kodlar/pharma-navigator/config.toml', 'rb') as f:
        return tomli.load(f)

CONFIG = load_config()

# Initialize LM
def init_lm():
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError("CEREBRAS_API_KEY not set")
    
    # Use the correct model name format for Cerebras
    return dspy.LM(
        model=f"cerebras/{CONFIG['llm']['model']}",
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1",
        temperature=CONFIG['llm']['temperature'],
        max_tokens=CONFIG['llm']['max_tokens']
    )

def main():
    print("=" * 60)
    print(" 💊 Pharma Navigator - Backend Test")
    print("=" * 60)
    
    # Initialize
    print("\n🔧 Initializing components...")
    lm = init_lm()
    dspy.configure(lm=lm)
    retriever = DrugRetriever(
        db_path=CONFIG['database']['path'],
        embedding_model=CONFIG['embedding']['model']
    )
    
    stats = retriever.get_collection_stats()
    print(f"✅ Database loaded: {stats['total_chunks']} chunks from {len(stats['unique_drugs'])} drugs")
    print(f"   Drugs: {', '.join(stats['unique_drugs'])}")
    
    # Test queries
    test_queries = [
        "Arvales yan etkileri nelerdir?",
        "Cipralex nasıl kullanılır?",
        "Hava bugün nasıl?",  # Should be rejected
    ]
    
    print("\n" + "=" * 60)
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        print("-" * 60)
        
        # Step 1: Intent Classification
        print("🎯 Intent Classification...")
        intent_result = classify_intent(query, lm)
        print(f"   Is drug-related: {intent_result['is_drug_related']}")
        if intent_result['is_drug_related']:
            print(f"   Detected drugs: {intent_result['drug_names']}")
            
            # Step 2: Retrieval
            print("\n🔍 Retrieving relevant chunks...")
            retrieval_result = retriever.retrieve(
                query=query,
                drug_names=intent_result['drug_names'] if intent_result['drug_names'] else None,
                top_k=CONFIG['retrieval']['top_k'],
                similarity_threshold=CONFIG['retrieval']['similarity_threshold']
            )
            
            chunks = retrieval_result['chunks']
            if chunks:
                print(f"   Found {len(chunks)} relevant chunks:")
                for j, chunk in enumerate(chunks[:3], 1):
                    print(f"   {j}. {chunk['metadata']['drug_name']} - {chunk['metadata']['section'][:50]}...")
                
                # Step 3: Generation
                print("\n💬 Generating answer...")
                context = retriever.format_context(chunks)
                answer_result = generate_answer(
                    question=query,
                    context=context,
                    lm=lm,
                    check_confidence=True
                )
                
                print(f"   Confidence: {answer_result['confidence']}")
                print(f"   Answer preview: {answer_result['answer'][:100]}...")
            else:
                print("   No relevant chunks found (below threshold)")
        else:
            print(f"   ❌ Off-topic: {intent_result['refusal_message']}")
    
    print("\n" + "=" * 60)
    print("✅ All components working correctly!")
    print("=" * 60)

if __name__ == "__main__":
    main()
