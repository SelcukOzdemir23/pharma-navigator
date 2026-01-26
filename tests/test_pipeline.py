"""Tam sistem test - Retrieval + Vectorization doğrulaması."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.retriever import DrugRetriever
from src.retrieval.embedder import get_embedder
from src.retrieval.chunker import chunk_drug_document


def test_end_to_end_flow():
    """Uçtan uca akış."""
    print("\n" + "=" * 70)
    print("🚀 END-TO-END TEST: Retrieval + Vectorization Flow")
    print("=" * 70)
    
    # 1. Load retriever
    print("\n[1/5] Loading retriever...")
    retriever = DrugRetriever()
    stats = retriever.get_collection_stats()
    print(f"  ✓ Database loaded with {stats['total_chunks']} chunks")
    
    # 2. Example drug questions
    print("\n[2/5] Testing with real drug questions...")
    questions = [
        ("Arvales yan etkileri nelerdir?", "Arvales"),
        ("Cipralex nasıl kullanılır?", "Cipralex"),
        ("Augmentin için uyarılar?", "Augmentin"),
    ]
    
    for question, expected_drug in questions:
        result = retriever.retrieve(
            query=question,
            similarity_threshold=0.6,
            top_k=3
        )
        
        print(f"\n  Q: {question}")
        print(f"  Expected drug: {expected_drug}")
        print(f"  Detected drugs: {result['drug_names']}")
        print(f"  Chunks found: {len(result['chunks'])}")
        
        if result['chunks']:
            print(f"  Top score: {result['max_score']:.4f}")
            # Check if retrieved chunks are from expected drug
            retrieved_drugs = set(c['metadata']['drug_name'] for c in result['chunks'])
            print(f"  Retrieved from: {retrieved_drugs}")
            
            if expected_drug in retrieved_drugs:
                print("  ✓ Correct drug retrieved!")
            else:
                print("  ⚠️  Different drug retrieved")
    
    # 3. Cross-drug test
    print("\n[3/5] Testing cross-drug filtering...")
    
    # Same query with different drug filters
    test_query = "yan etkileri"
    drugs_to_test = ["Arvales", "Cipralex", "Augmentin"]
    
    print(f"\n  Query: '{test_query}'")
    print(f"  Testing filtering for: {drugs_to_test}")
    
    for drug in drugs_to_test:
        result = retriever.retrieve(
            query=test_query,
            drug_names=[drug],
            similarity_threshold=0.5,
            top_k=5
        )
        
        # Verify all chunks belong to the specified drug
        all_correct = all(
            chunk['metadata']['drug_name'] == drug 
            for chunk in result['chunks']
        )
        
        status = "✓" if all_correct else "✗"
        print(f"\n  {status} {drug}: {len(result['chunks'])} chunks (all correct: {all_correct})")
    
    # 4. Similarity score analysis
    print("\n[4/5] Analyzing similarity score distribution...")
    
    sample_queries = [
        "kullanım",
        "yan etkiler",
        "uyarılar",
        "doz",
        "kontrendikasyon",
    ]
    
    print(f"\n  Testing {len(sample_queries)} different keyword queries...")
    
    for query_word in sample_queries:
        result = retriever.retrieve(
            query=query_word,
            similarity_threshold=0.5,
            top_k=10
        )
        
        if result['chunks']:
            scores = [c['score'] for c in result['chunks']]
            avg_score = sum(scores) / len(scores)
            num_chunks = len(result['chunks'])
            min_score = min(scores)
            max_score = max(scores)
            print(f"  '{query_word:15}': {num_chunks:2d} chunks, "
                  f"avg score {avg_score:.4f}, range [{min_score:.3f}, {max_score:.3f}]")
        else:
            print(f"  '{query_word:15}': No results")
    
    # 5. Vectorization quality
    print("\n[5/5] Verifying vectorization quality...")
    
    embedder = get_embedder()
    
    # Test same text twice -> should have identical embedding
    test_text = "Arvales yan etkileri nedir?"
    emb1 = embedder.embed_single(test_text)
    emb2 = embedder.embed_single(test_text)
    
    import numpy as np
    diff = np.abs(np.array(emb1) - np.array(emb2)).max()
    print(f"\n  Embedding consistency (same text x2):")
    print(f"    Max difference: {diff:.10f}")
    print(f"    Status: {'✓ Perfect' if diff < 1e-6 else '⚠️  Slight variation'}")
    
    # Test semantic similarity
    similar_texts = [
        "Arvales'in yan etkileri nelerdir?",
        "Arvales'in istenmeyen etkileri?",
        "Arvales kullanan kişilerde neler görülür?",
    ]
    
    baseline_emb = embedder.embed_single(similar_texts[0])
    
    print(f"\n  Semantic similarity (similar texts):")
    for text in similar_texts[1:]:
        text_emb = embedder.embed_single(text)
        sim = np.dot(baseline_emb, text_emb) / (
            np.linalg.norm(baseline_emb) * np.linalg.norm(text_emb)
        )
        print(f"    '{text[:40]}': {sim:.4f}")
    
    # Test dissimilar texts
    print(f"\n  Semantic similarity (dissimilar texts):")
    dissimilar_texts = [
        "Hava bugün nasıl?",
        "2+2 kaç eder?",
        "Messi kaç gol attı?",
    ]
    
    for text in dissimilar_texts:
        text_emb = embedder.embed_single(text)
        sim = np.dot(baseline_emb, text_emb) / (
            np.linalg.norm(baseline_emb) * np.linalg.norm(text_emb)
        )
        print(f"    '{text[:40]}': {sim:.4f}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_end_to_end_flow()
