"""FAISS-based retrieval for drug information (Python 3.14 compatible)."""

import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import pickle
import re

from .embedder import get_embedder


class DrugRetriever:
    """İlaç bilgilerini FAISS ile retrieve eder.
    
    ChromaDB yerine FAISS kullanır (Python 3.14 uyumlu).
    Metadata filtering manuel olarak yapılır.
    """
    
    def __init__(
        self,
        db_path: str = "./faiss_db",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    ):
        """
        Args:
            db_path: FAISS index ve metadata storage yolu
            embedding_model: Embedding model adı
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        self.embedder = get_embedder(model_name=embedding_model)
        
        self.index_file = self.db_path / "faiss.index"
        self.metadata_file = self.db_path / "metadata.pkl"
        
        # Load existing index or create new
        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create empty index
            self.index = faiss.IndexFlatIP(self.embedder.dimension)  # Inner Product (cosine similarity)
            self.metadata = []
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, str]]
    ):
        """Dokümanları index'e ekler.
        
        Args:
            texts: Chunk metinleri
            metadatas: Her chunk için metadata dict
        """
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.embedder.embed(texts)
        embeddings_np = np.array(embeddings, dtype='float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_np)
        
        # Add to index
        self.index.add(embeddings_np)
        
        # Store metadata
        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            self.metadata.append({
                'text': text,
                **meta,
                'index': len(self.metadata)
            })
    
    def save(self):
        """Index ve metadata'yı diske kaydeder."""
        faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def clear(self):
        """Index ve metadata'yı temizler."""
        self.index.reset()
        self.metadata = []
        
        if self.index_file.exists():
            self.index_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
    
    def extract_drug_names_from_query(self, query: str) -> List[str]:
        """Sorgudan ilaç isimlerini çıkarır."""
        potential_drugs = re.findall(r'\b[A-Z][a-zçğıöşü]+\b', query)
        return potential_drugs
    
    def retrieve(
        self,
        query: str,
        drug_names: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
        section_filter: Optional[str] = None
    ) -> Dict:
        """İlaç bilgilerini retrieve eder.
        
        Args:
            query: Kullanıcı sorusu
            drug_names: İlaç isimleri (None ise otomatik tespit)
            top_k: Kaç chunk getirilecek
            similarity_threshold: Minimum benzerlik skoru
            section_filter: Bölüm filtresi
            
        Returns:
            {
                'chunks': [{'text': ..., 'metadata': ..., 'score': ...}],
                'drug_names': [...],
                'max_score': float
            }
        """
        if self.index.ntotal == 0:
            return {
                'chunks': [],
                'drug_names': [],
                'max_score': 0.0
            }
        
        # Query embedding
        query_embedding = self.embedder.embed_single(query)
        query_np = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_np)
        
        # İlaç isimlerini tespit et
        if drug_names is None:
            drug_names = self.extract_drug_names_from_query(query)
        
        # Search in FAISS (get more for filtering)
        k = min(top_k * 4, self.index.ntotal)
        scores, indices = self.index.search(query_np, k)
        
        # Filter and format results
        chunks = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
            
            meta = self.metadata[idx]
            
            # Apply filters
            if drug_names:
                if meta['drug_name'] not in drug_names:
                    continue
            
            if section_filter:
                if meta['section'] != section_filter:
                    continue
            
            # Threshold check
            if score >= similarity_threshold:
                chunks.append({
                    'text': meta['text'],
                    'metadata': {
                        'drug_name': meta['drug_name'],
                        'section': meta['section'],
                        'chunk_id': meta['chunk_id'],
                        'source_file': meta['source_file']
                    },
                    'score': float(score),
                    'id': str(idx)
                })
        
        # Sort by score and limit
        chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)[:top_k]
        
        max_score = chunks[0]['score'] if chunks else 0.0
        
        return {
            'chunks': chunks,
            'drug_names': drug_names,
            'max_score': max_score
        }
    
    def format_context(self, chunks: List[Dict]) -> str:
        """Retrieve edilen chunk'ları LLM için context formatına dönüştürür."""
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            context_parts.append(
                f"[{i}] **{metadata['drug_name']}** - {metadata['section']}\n"
                f"{chunk['text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_collection_stats(self) -> Dict:
        """Collection istatistiklerini döndürür."""
        unique_drugs = set(m['drug_name'] for m in self.metadata)
        
        return {
            'total_chunks': len(self.metadata),
            'unique_drugs': sorted(list(unique_drugs)),
            'collection_name': 'faiss_index'
        }
