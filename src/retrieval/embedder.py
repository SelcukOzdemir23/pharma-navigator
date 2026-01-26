"""Embedding model for Turkish text."""

from sentence_transformers import SentenceTransformer
from typing import List, Optional
import torch


class TurkishEmbedder:
    """Türkçe metinler için embedding modeli.
    
    paraphrase-multilingual-mpnet-base-v2 modelini kullanır,
    bu model Türkçe için oldukça iyi performans gösterir.
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        device: str = "cpu"
    ):
        """
        Args:
            model_name: HuggingFace model adı
            device: 'cpu' veya 'cuda'
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Metinleri vektörlere dönüştürür.
        
        Args:
            texts: Vektörlenecek metin listesi
            
        Returns:
            Embedding vektörleri (her biri self.dimension boyutunda)
        """
        if not texts:
            return []
        
        # Batch encoding
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def embed_single(self, text: str) -> List[float]:
        """Tek bir metni vektörleştirir.
        
        Args:
            text: Vektörlenecek metin
            
        Returns:
            Embedding vektörü
        """
        return self.embed([text])[0]


# Global instance (lazy loading)
_embedder: Optional[TurkishEmbedder] = None


def get_embedder(
    model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    device: str = "cpu"
) -> TurkishEmbedder:
    """Global embedder instance'ını döndürür (singleton pattern).
    
    Args:
        model_name: HuggingFace model adı
        device: 'cpu' veya 'cuda'
        
    Returns:
        TurkishEmbedder instance
    """
    global _embedder
    
    if _embedder is None:
        _embedder = TurkishEmbedder(model_name=model_name, device=device)
    
    return _embedder
