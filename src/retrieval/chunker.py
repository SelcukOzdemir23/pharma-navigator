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
    
    # Daha güçlü pattern matching
    section_patterns = {
        "yan etkiler": [
            "yan etki", "olası yan", "istenmeyen etki", "adverse", 
            "side effect", "yan tesir", "olumsuz etki"
        ],
        "kullanım": [
            "nasıl kullan", "kullanım şekli", "doz", "dozaj", "uygulama", 
            "alınır", "verilir", "enjekte", "tablet", "mg", "günde", 
            "sabah", "akşam", "aç", "tok", "yemek"
        ],
        "bileşim": [
            "bileşim", "etkin madde", "içindekiler", "yardımcı madde", 
            "aktif madde", "formül", "mg", "içerir", "eşdeğer"
        ],
        "uyarılar": [
            "uyar", "dikkat", "kullanmadan önce", "kullanmayınız", 
            "kontrendik", "yasak", "tehlike", "risk", "sakın"
        ],
        "etkileşimler": [
            "etkileşim", "diğer ilaçlar", "birlikte kullan", "beraber", 
            "kombinasyon", "ilaç ilaç", "alkol", "gıda"
        ],
        "doz aşımı": [
            "doz aşımı", "fazla kullan", "aşırı doz", "overdoz", 
            "zehirlenme", "intoksikasyon"
        ],
        "saklama": [
            "saklama", "muhafaza", "son kullanma", "depolama", 
            "sıcaklık", "ışık", "nem", "çocuk"
        ],
        "endikasyonlar": [
            "ne için kullan", "nedir", "endikasyon", "tedavi", 
            "hastalık", "semptom", "belirti", "şikayet"
        ]
    }
    
    # Skorlama sistemi - birden fazla keyword eşleşirse daha güvenilir
    section_scores = {}
    for section, keywords in section_patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            section_scores[section] = score
    
    if section_scores:
        # En yüksek skoru alan bölümü döndür
        return max(section_scores, key=section_scores.get)
    
    return "genel"


def detect_section_from_heading(heading: str) -> str:
    """Başlık metninden bölüm tespiti (heading sinyali baskın)."""
    if not heading:
        return "genel"

    h = heading.lower()
    if any(k in h for k in ["yan etki", "istenmeyen"]):
        return "yan etkiler"
    if any(k in h for k in ["doz aşımı", "fazla kullan", "aşırı doz"]):
        return "doz aşımı"
    if any(k in h for k in ["kullanmadan önce", "dikkat", "uyarı"]):
        return "uyarılar"
    if any(k in h for k in ["etkileşim", "birlikte kullan", "diğer ilaç"]):
        return "etkileşimler"
    if any(k in h for k in ["saklama", "muhafaza", "son kullanma"]):
        return "saklama"
    if any(k in h for k in ["bileşim", "etkin madde", "yardımcı madde", "içindekiler"]):
        return "bileşim"
    if any(k in h for k in ["ne için kullan", "nedir", "endikasyon"]):
        return "endikasyonlar"
    if any(k in h for k in ["nasıl kullan", "doz", "uygulama"]):
        return "kullanım"
    return "genel"


def _split_markdown_sections(content: str) -> List[Dict[str, str]]:
    """Başlığı ve gövdesiyle birlikte markdown bölümlerini döndürür."""
    pattern = re.compile(r"(^#{1,3}\s+.+$)", re.MULTILINE)
    matches = list(pattern.finditer(content))
    sections: List[Dict[str, str]] = []

    if not matches:
        text = content.strip()
        if text:
            sections.append({"heading": None, "text": text})
        return sections

    for idx, match in enumerate(matches):
        heading_line = match.group(1).strip()
        heading_text = heading_line.lstrip('#').strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        combined = heading_line + "\n" + body if body else heading_line
        sections.append({"heading": heading_text, "text": combined.strip()})

    return sections


def chunk_drug_document(
    file_path: str,
    chunk_size: int = 1800,
    chunk_overlap: int = 200,
    min_chunk_chars: int = 300
) -> List[Dict[str, str]]:
    """İlaç prospektüsünü basit ve etkili şekilde chunk'lara böler."""
    drug_name = extract_drug_name(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basit sliding window chunking
    chunks = []
    chunk_id = 0
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # Cümle sonunda kes
        if end < len(content):
            for i in range(end, max(start + chunk_size//2, end - 200), -1):
                if content[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk_text = content[start:end].strip()
        
        if len(chunk_text) >= min_chunk_chars:
            section = detect_section(chunk_text)
            
            chunks.append({
                'text': chunk_text,
                'drug_name': drug_name,
                'section': section,
                'chunk_id': chunk_id,
                'source_file': str(Path(file_path).name)
            })
            chunk_id += 1
        
        start = end - chunk_overlap if end < len(content) else end
    
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
