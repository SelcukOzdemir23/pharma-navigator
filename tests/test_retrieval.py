"""Retrieval ve embedding testi.

Vektörleme işleminin doğru çalıştığını kontrol eder.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.retriever import DrugRetriever
from src.retrieval.embedder import get_embedder


def test_embedding_quality():
    """Embedding modeline test verelim."""
    print("\n🧪 TEST 1: Embedding Modeli")
    print("=" * 60)
    
    embedder = get_embedder()
    
    # Test queries
    test_queries = [
        "Arvales yan etkileri nelerdir?",
        "Cipralex nasıl kullanılır?",
        "Bu ilaç bana uyar mı?",
    ]
    
    for query in test_queries:
        embedding = embedder.embed_single(query)
        print(f"\n✓ Query: '{query}'")
        print(f"  Embedding boyutu: {len(embedding)}")
        print(f"  İlk 5 değer: {embedding[:5]}")
        print(f"  Min: {min(embedding):.4f}, Max: {max(embedding):.4f}")


def test_retrieval_basic():
    """Temel retrieval testi."""
    print("\n\n🧪 TEST 2: Temel Retrieval")
    print("=" * 60)
    
    retriever = DrugRetriever()
    stats = retriever.get_collection_stats()
    
    print(f"\n✓ Database Durumu:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Unique drugs: {len(stats['unique_drugs'])}")
    print(f"  Drugs: {', '.join(stats['unique_drugs'])}")


def test_retrieval_query():
    """Gerçek sorgu testi."""
    print("\n\n🧪 TEST 3: Sorgu Testi")
    print("=" * 60)
    
    retriever = DrugRetriever()
    
    test_cases = [
        {
            "query": "Arvales yan etkileri",
            "expected_drug": "Arvales"
        },
        {
            "query": "Cipralex nasıl kullanılır",
            "expected_drug": "Cipralex"
        },
        {
            "query": "Augmentin bileşimi",
            "expected_drug": "Augmentin"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        query = test['query']
        expected = test['expected_drug']
        
        result = retriever.retrieve(
            query=query,
            top_k=5,
            similarity_threshold=0.6
        )
        
        print(f"\n✓ Test {i}: '{query}'")
        print(f"  Beklenen ilaç: {expected}")
        print(f"  Bulunan chunk sayısı: {len(result['chunks'])}")
        print(f"  Tespit edilen ilaçlar: {result['drug_names'] if result['drug_names'] else 'Otomatik'}")
        
        if result['chunks']:
            print(f"  Max benzerlik skoru: {result['max_score']:.4f}")
            print(f"\n  📄 Bulunmuş bölümler:")
            
            for j, chunk in enumerate(result['chunks'][:3], 1):
                meta = chunk['metadata']
                print(f"\n     [{j}] {meta['drug_name']} - {meta['section']} ({chunk['score']:.4f})")
                print(f"         Text: {chunk['text'][:100]}...")
        else:
            print("  ⚠️  Sonuç bulunamadı!")


def test_metadata_filtering():
    """Metadata filtering testi."""
    print("\n\n🧪 TEST 4: Metadata Filtering")
    print("=" * 60)
    
    retriever = DrugRetriever()
    
    # Aynı sorguyu farklı ilaçlar için filtreleyelim
    query = "yan etki"
    
    test_drugs = ["Arvales", "Cipralex", "Augmentin"]
    
    for drug in test_drugs:
        result = retriever.retrieve(
            query=query,
            drug_names=[drug],
            top_k=3,
            similarity_threshold=0.5
        )
        
        print(f"\n✓ Query: '{query}' | Filter: {drug}")
        print(f"  Bulunan chunk: {len(result['chunks'])}")
        
        if result['chunks']:
            print(f"  Max skor: {result['max_score']:.4f}")
            print(f"  Bölümler: {[c['metadata']['section'] for c in result['chunks']]}")
            
            # Tüm sonuçların aynı ilaç olmasını kontrol et
            all_same_drug = all(c['metadata']['drug_name'] == drug for c in result['chunks'])
            print(f"  ✓ Filtering doğru: {all_same_drug}")
        else:
            print("  ⚠️  Sonuç bulunamadı")


def test_semantic_similarity():
    """Semantic benzerlik testi."""
    print("\n\n🧪 TEST 5: Semantic Benzerlik")
    print("=" * 60)
    
    retriever = DrugRetriever()
    embedder = get_embedder()
    
    # Semantic olarak yakın cümleler
    similar_queries = [
        "Arvales yan etkileri nelerdir?",
        "Arvales'in istenmeyen etkileri?",
        "Arvales kullanan kişiler ne hissederler?",
        "Arvales güvenli mi?",  # Bu daha farklı olmalı
    ]
    
    print(f"\nArvales için semantic benzerlik:")
    
    embeddings = embedder.embed(similar_queries)
    
    # Embedding'ler arasında benzerlik (cosine similarity)
    import numpy as np
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    baseline = embeddings[0]
    
    for i, (query, embedding) in enumerate(zip(similar_queries, embeddings), 1):
        sim = cosine_similarity(baseline, embedding)
        print(f"\n  {i}. '{query}'")
        print(f"     Benzerlik: {sim:.4f}")


def test_threshold_effect():
    """Threshold'un etkisini test et."""
    print("\n\n🧪 TEST 6: Threshold Etkisi")
    print("=" * 60)
    
    retriever = DrugRetriever()
    query = "Arvales kullanımı ve dozaj"
    
    thresholds = [0.5, 0.6, 0.65, 0.7, 0.75]
    
    print(f"\nQuery: '{query}'")
    print(f"Drug: Arvales\n")
    
    for threshold in thresholds:
        result = retriever.retrieve(
            query=query,
            drug_names=["Arvales"],
            top_k=10,
            similarity_threshold=threshold
        )
        
        print(f"  Threshold {threshold:.2f}: {len(result['chunks'])} chunk(s)", end="")
        if result['chunks']:
            print(f" (max skor: {result['max_score']:.4f})")
        else:
            print()


def main():
    """Tüm testleri çalıştır."""
    print("\n" + "=" * 60)
    print("💊 Pharma Navigator - Retrieval & Embedding Tests")
    print("=" * 60)
    
    try:
        test_embedding_quality()
        test_retrieval_basic()
        test_retrieval_query()
        test_metadata_filtering()
        test_semantic_similarity()
        test_threshold_effect()
        
        print("\n\n" + "=" * 60)
        print("✅ Tüm testler başarılı!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
