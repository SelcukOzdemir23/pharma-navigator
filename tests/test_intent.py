"""Intent classification testi."""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.models.intent import classify_intent
import dspy


def test_drug_related_queries():
    """İlaç ile ilgili sorular için test."""
    print("\n🧪 TEST 1: İlaç ile İlgili Sorular")
    print("=" * 60)
    
    # Setup LLM with modern dspy.LM client
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found in .env")
        return
    
    lm = dspy.LM(
        model="openai/llama3.1-8b",
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1"
    )
    
    drug_queries = [
        "Arvales yan etkileri nelerdir?",
        "Cipralex nasıl kullanılır?",
        "Augmentin bana uyar mı?",
        "Hangi ilaçlar birbiriyle etkileşim gösterir?",
        "Janumet fiyatı ne kadar?",
    ]
    
    for query in drug_queries:
        result = classify_intent(query, lm=lm)
        print(f"\n✓ Query: '{query}'")
        print(f"  Is Drug Related: {result['is_drug_related']}")
        print(f"  Detected Drugs: {result['drug_names']}")
        print(f"  Reasoning: {result['reasoning'][:100] if result['reasoning'] else 'N/A'}...")


def test_non_drug_queries():
    """İlaç ile ilgili olmayan sorular."""
    print("\n\n🧪 TEST 2: İlaç İle İlgili Olmayan Sorular")
    print("=" * 60)
    
    # Setup LLM with modern dspy.LM client
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found in .env")
        return
    
    lm = dspy.LM(
        model="openai/llama3.1-8b",
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1"
    )
    
    non_drug_queries = [
        "Hava bugün nasıl?",
        "2+2 kaç eder?",
        "Messi kaç gol attı?",
        "İstanbul'un nüfusu ne kadar?",
        "Türk bayrağının anlamı nedir?",
    ]
    
    for query in non_drug_queries:
        result = classify_intent(query, lm=lm)
        print(f"\n✓ Query: '{query}'")
        print(f"  Is Drug Related: {result['is_drug_related']}")
        print(f"  Response: {result.get('response', 'N/A')[:100]}...")


def test_ambiguous_queries():
    """Belirsiz sorular."""
    print("\n\n🧪 TEST 3: Belirsiz Sorular")
    print("=" * 60)
    
    # Setup LLM with modern dspy.LM client
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found in .env")
        return
    
    lm = dspy.LM(
        model="openai/llama3.1-8b",
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1"
    )
    
    ambiguous_queries = [
        "Türkiye'de en çok kullanılan ilaçlar?",  # İlaç ama genel
        "Corona tedavisi nedir?",  # Hastalık + tedavi
        "Grip için ne yapmalı?",  # Hastalık soru
        "Aspirin nedir?",  # İlaç ama basit
    ]
    
    for query in ambiguous_queries:
        result = classify_intent(query, lm=lm)
        print(f"\n✓ Query: '{query}'")
        print(f"  Is Drug Related: {result['is_drug_related']}")
        print(f"  Detected Drugs: {result['drug_names']}")


def main():
    print("\n" + "=" * 60)
    print("🎯 Pharma Navigator - Intent Classification Tests")
    print("=" * 60)
    
    try:
        test_drug_related_queries()
        test_non_drug_queries()
        test_ambiguous_queries()
        
        print("\n\n" + "=" * 60)
        print("✅ Intent classification testi tamamlandı!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
