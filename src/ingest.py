"""Ingest drug documents into ChromaDB.

Bu script, data/pdfs/ klasöründeki ilaç prospektüslerini okur,
chunk'lara böler, embedlingleri oluşturur ve ChromaDB'ye kaydeder.

Usage:
    python -m src.ingest
"""

import sys
from pathlib import Path
from typing import List
import tomli
from tqdm import tqdm

from src.retrieval.chunker import chunk_drug_document, get_chunk_metadata
from src.retrieval.embedder import get_embedder
from src.retrieval.retriever import DrugRetriever


def load_config(config_path: str = "config.toml") -> dict:
    """TOML config dosyasını yükler."""
    with open(config_path, 'rb') as f:
        return tomli.load(f)


def find_drug_files(source_dir: str, extensions: List[str]) -> List[Path]:
    """İlaç dosyalarını bulur.
    
    Args:
        source_dir: Kaynak dizin
        extensions: Desteklenen dosya uzantıları (örn: ['.md', '.txt'])
        
    Returns:
        Bulunan dosya yolları
    """
    source_path = Path(source_dir)
    files = []
    
    for ext in extensions:
        files.extend(source_path.glob(f'**/*{ext}'))
    
    return sorted(files)


def ingest_documents(config: dict) -> None:
    """İlaç dokümanlarını ChromaDB'ye yükler."""
    
    print("🔧 Pharma Navigator - Document Ingestion")
    print("=" * 50)
    
    # Config
    source_dir = config['data']['source_dir']
    extensions = config['data']['supported_formats']
    chunk_size = config['retrieval']['chunk_size']
    chunk_overlap = config['retrieval']['chunk_overlap']
    db_path = config['database']['path']
    collection_name = config['database']['collection_name']
    embedding_model = config['embedding']['model']
    
    # Find drug files
    print(f"\n📁 Scanning {source_dir} for drug documents...")
    drug_files = find_drug_files(source_dir, extensions)
    
    if not drug_files:
        print(f"❌ No drug files found in {source_dir}")
        print(f"   Supported formats: {', '.join(extensions)}")
        sys.exit(1)
    
    print(f"✅ Found {len(drug_files)} drug document(s):")
    for f in drug_files:
        print(f"   - {f.name}")
    
    # Initialize embedder
    print(f"\n🤖 Loading embedding model: {embedding_model}")
    embedder = get_embedder(
        model_name=embedding_model,
        device=config['embedding']['device']
    )
    print(f"✅ Model loaded (dimension: {embedder.dimension})")
    
    # Initialize retriever (FAISS-based)
    print(f"\n💾 Initializing FAISS index at {db_path}...")
    retriever = DrugRetriever(
        db_path=db_path,
        embedding_model=embedding_model
    )
    
    # Clear existing index (fresh start)
    print(f"🗑️  Clearing existing index...")
    retriever.clear()
    
    # Process each drug file
    print(f"\n📚 Processing documents...")
    total_chunks = 0
    
    for drug_file in tqdm(drug_files, desc="Ingesting"):
        # Chunk document
        chunks = chunk_drug_document(
            str(drug_file),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if not chunks:
            print(f"⚠️  No chunks created for {drug_file.name}")
            continue
        
        # Prepare for FAISS
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [get_chunk_metadata(chunk) for chunk in chunks]
        
        # Add to index
        retriever.add_documents(texts, metadatas)
        
        total_chunks += len(chunks)
    
    # Save index
    print(f"\n💾 Saving index...")
    retriever.save()
    
    # Stats
    print(f"\n📊 Ingestion Complete!")
    stats = retriever.get_collection_stats()
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Unique drugs: {len(stats['unique_drugs'])}")
    print(f"   Drugs: {', '.join(stats['unique_drugs'])}")
    print(f"\n✅ Database ready at: {db_path}")


def main():
    """Main entry point."""
    try:
        config = load_config()
        ingest_documents(config)
    except FileNotFoundError:
        print("❌ Error: config.toml not found")
        print("   Make sure you're running from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
