"""Document chunking for drug prospectuses."""

import re
from typing import List, Dict
from pathlib import Path


def extract_drug_name(file_path: str) -> str:
    """Dosya adından ilaç ismini çıkarır.
    
    Args:
        file_path: İlaç dosyasının yolu (örn: data/pdfs/Arvales.md)
        
    Returns:
        İlaç ismi (örn: "Arvales")
    """
    return Path(file_path).stem


def detect_section(text: str) -> str:
    """Metin parçasının hangi bölümden geldiğini tespit eder.
    
    Args:
        text: Prospektüs metin parçası
        
    Returns:
        Bölüm adı (örn: "yan etkiler", "kullanım", "uyarılar")
    """
    text_lower = text.lower()
    
    # Bölüm başlıklarını tespit et
    section_patterns = {
        "kullanım": ["kullan", "nasıl kullan", "doz", "uygulama"],
        "yan etkiler": ["yan etki", "olası yan", "istenmeyen etki"],
        "uyarılar": ["uyar", "dikkat", "kullanmadan önce", "kullanmayınız"],
        "etkileşimler": ["etkileşim", "diğer ilaçlar", "birlikte kullan"],
        "bileşim": ["bileşim", "etkin madde", "içindekiler", "yardımcı madde"],
        "saklama": ["saklama", "muhafaza", "son kullanma"],
        "genel bilgi": ["nedir", "ne için kullan", "tanım", "özet"]
    }
    
    for section, keywords in section_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            return section
    
    return "genel"


def chunk_drug_document(
    file_path: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict[str, str]]:
    """İlaç prospektüsünü metadata ile chunk'lara böler.
    
    Args:
        file_path: İlaç dosyasının yolu
        chunk_size: Chunk boyutu (karakter)
        chunk_overlap: Chunk'lar arası örtüşme
        
    Returns:
        Her biri şu anahtarları içeren dict listesi:
        - text: Chunk metni
        - drug_name: İlaç ismi
        - section: Bölüm adı
        - chunk_id: Chunk numarası
        - source_file: Kaynak dosya
    """
    drug_name = extract_drug_name(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Markdown başlıklarına göre bölümleri ayır
    sections = re.split(r'\n#{1,3}\s+', content)
    
    chunks = []
    chunk_id = 0
    
    for section in sections:
        if not section.strip():
            continue
        
        # Her bölümü daha küçük chunk'lara böl
        section_text = section.strip()
        start = 0
        
        while start < len(section_text):
            end = start + chunk_size
            
            # Cümle ortasında bölmemek için son nokta/yeni satırı bul
            if end < len(section_text):
                # Geriye doğru son cümle sonu karakterini ara
                for i in range(end, start + chunk_size // 2, -1):
                    if section_text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk_text = section_text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'drug_name': drug_name,
                    'section': detect_section(chunk_text),
                    'chunk_id': chunk_id,
                    'source_file': str(Path(file_path).name)
                })
                chunk_id += 1
            
            # Overlap ile bir sonraki chunk'a geç
            start = end - chunk_overlap if end < len(section_text) else end
    
    return chunks


def get_chunk_metadata(chunk: Dict[str, str]) -> Dict[str, str]:
    """Chunk'ın metadata'sını döndürür (ChromaDB için).
    
    Args:
        chunk: chunk_drug_document'ten dönen dict
        
    Returns:
        ChromaDB metadata formatında dict
    """
    return {
        'drug_name': chunk['drug_name'],
        'section': chunk['section'],
        'chunk_id': str(chunk['chunk_id']),
        'source_file': chunk['source_file']
    }
