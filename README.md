# 💊 Pharma Navigator

**Modern RAG-tabanlı ilaç prospektüsü bilgi asistanı**

Yüksek lisans projesi kapsamında geliştirilmiş, **metadata-aware retrieval** ve **intent classification** ile güçlendirilmiş yapay zeka asistanı. Türkçe ilaç prospektüslerini analiz eder ve sadece ilaç soruları yanıtlar.

## 🎯 Proje Hakkında

Bu sistem, **Information Retrieval** ve **Explainable AI** konseptlerini modern teknolojilerle birleştirerek şu sorunları çözer:

- ✅ İlaç bilgilerinin hızlı ve doğru erişimi
- ✅ Alakasız soruların otomatik reddedilmesi (intent classification)
- ✅ İlaç isimlerine göre akıllı filtreleme (metadata-aware retrieval)
- ✅ Kaynak şeffaflığı ve açıklanabilirlik (explainable steps)

### 🏗️ Teknik Mimari

```
┌─────────────────────────────────────────┐
│     Chainlit UI (Explainable Steps)     │
└──────────────┬──────────────────────────┘
               │
    ┌──────────▼──────────┐
    │  DSPy Signatures    │
    ├─────────────────────┤
    │ • IntentClassifier  │ ← İlaç sorusu mu?
    │ • DrugQA            │ ← Yanıt oluştur
    │ • ConfidenceChecker │ ← Güvenilirlik
    └──────────┬──────────┘
               │
    ┌──────────▼──────────────┐
    │  Custom Retrieval       │
    ├─────────────────────────┤
    │ • Drug Name Extractor   │
    │ • Metadata Filter       │
    │ • Semantic Search       │
    │ • Confidence Scoring    │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │  FAISS Index            │
    │  + Metadata (pickle)    │
    │  + Turkish Embeddings   │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │  Cerebras LLM API       │
    └─────────────────────────┘
```

### 🔧 Teknoloji Stack

| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| **LLM Orchestration** | DSPy 2.5+ | Signature-based prompt engineering |
| **LLM Engine** | Cerebras (Llama-3.1-8B) | Ultra-hızlı inference |
| **Vector DB** | FAISS | Local, fast, Python 3.14 compatible |
| **Embeddings** | sentence-transformers | Türkçe semantic search |
| **UI** | Chainlit | Explainable multi-step interface |
| **Config** | TOML | Merkezi yapılandırma |

## 🚀 Kurulum

### 1. Gereksinimler
- Python 3.10+ (3.12 önerilir)
- Cerebras API Anahtarı ([buradan alın](https://cloud.cerebras.ai/))

### 2. Sanal Ortam Oluştur
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 4. Çevre Değişkenlerini Ayarla
`.env` dosyası oluşturun:
```bash
CEREBRAS_API_KEY=csk-your-api-key-here
```

### 5. Veritabanını Oluştur
İlaç prospektüslerini ChromaDB'ye yükleyin:
```bash
python -m src.ingest
```

**Çıktı örneği:**
```
🔧 Pharma Navigator - Document Ingestion
==================================================

📁 Scanning ./data/pdfs for drug documents...
✅ Found 6 drug document(s):
   - Arvales.md
   - Augmentin.md
   - Cipralex.md
   - Coraspin.md
   - Enfluvir.md
   - Janumet.md

🤖 Loading embedding model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
✅ Model loaded (dimension: 768)

📚 Processing documents...
Ingesting: 100%|████████████| 6/6 [00:15<00:00]

📊 Ingestion Complete!
   Total chunks: 143
   Unique drugs: 6
   Drugs: Arvales, Augmentin, Cipralex, Coraspin, Enfluvir, Janumet

✅ Database ready at: ./chroma_db
```

### 6. Uygulamayı Çalıştır
```bash
chainlit run src/app.py -w
```

Tarayıcınızda `http://localhost:8000` açılacak.

## 📁 Proje Yapısı

```
pharma-navigator/
├── config.toml              # Merkezi yapılandırma (TOML)
├── .env                     # API anahtarları (git'e eklenmez)
├── requirements.txt         # Python bağımlılıkları
│
├── src/
│   ├── __init__.py
│   ├── app.py              # Chainlit uygulaması (ana giriş)
│   ├── ingest.py           # Veri yükleme script'i
│   │
│   ├── models/             # DSPy signatures
│   │   ├── __init__.py
│   │   ├── intent.py       # Intent classification
│   │   └── qa.py           # Question answering
│   │
│   └── retrieval/          # Retrieval pipeline
│       ├── __init__.py
│       ├── chunker.py      # Document chunking
│       ├── embedder.py     # Turkish embeddings
│       └── retriever.py    # Metadata-aware retrieval
│
├── data/
│   └── pdfs/               # İlaç prospektüsleri (Markdown)
│       ├── Arvales.md
│       ├── Augmentin.md
│       └── ...
│
├── faiss_db/               # FAISS index storage (otomatik oluşur)
└── tests/                  # Unit tests (opsiyonel)
```

## 🎨 Kullanım

### Örnek Sorular

✅ **İyi sorular** (sistem yanıtlar):
- "Arvales'in yan etkileri nelerdir?"
- "Cipralex nasıl kullanılır?"
- "Janumet'i kimler kullanamaz?"
- "Augmentin ile alkol kullanılabilir mi?"

❌ **Kötü sorular** (sistem reddeder):
- "Hava durumu nasıl?"
- "Python'da liste nasıl oluşturulur?"
- "Kahve sağlıklı mı?"

### Hızlı Deneme Seti (her ilaç için)
- **Arvales**: "Arvales nedir ve ne için kullanılır?" · "Arvales nasıl uygulanır, IV/IM farkı?" · "Arveles'in sık yan etkileri neler?"
- **Augmentin**: "Augmentin'in yaygın yan etkileri?" · "Augmentin ile alkol/varfarin birlikte olur mu?"
- **Cipralex**: "Cipralex'i kimler kullanmamalı (MAOI, kalp ritmi)?" · "Cipralex aç/tok alınır mı?" · "Cipralex araç kullanımı etkiler mi?"
- **Coraspin**: "Coraspin kimlerde kontrendike?" · "Coraspin'in kanama riski uyarıları neler?"
- **Enfluvir**: "Enfluvir nasıl alınır, doz aralığı nedir?" · "Enfluvir'in yaygın yan etkileri?"
- **Janumet**: "Janumet yemekle mi alınmalı?" · "Janumet'te laktik asidoz riskini artıran durumlar?" · "Janumet hamilelikte kullanılabilir mi?"

**Beklenen çıktı**: Debug bölümünde doğru ilaç adı, ilgili bölüm (kullanım/uyarılar/yan etkiler) ve skorların ~0.6-0.8+ görünmesi; yanıt tarafında kısa, net ve kaynaklı özet.

### Chainlit UI Özellikleri

Sistem 3 adımda çalışır ve her adım görselleştirilir:

1. **🎯 Intent Sınıflandırma**
   - Sorunun ilaçla ilgili olup olmadığını kontrol eder
   - İlaç isimlerini tespit eder
   - Alakasız sorular nazikçe reddedilir

2. **🔍 Bilgi Arama**
   - Prospektüslerde semantic search yapar
   - İlaç ismine göre filtreler (metadata)
   - Benzerlik skorlarını gösterir

3. **💬 Yanıt Oluşturma**
   - DSPy ChainOfThought ile yanıt üretir
   - Güvenilirlik seviyesi hesaplar
   - Kaynak bölümleri gösterir

## ⚙️ Yapılandırma

[config.toml](config.toml) dosyasından ayarlar yapabilirsiniz:

```toml
[retrieval]
chunk_size = 800              # Chunk boyutu (karakter)
chunk_overlap = 150           # Chunk overlap
top_k = 5                     # Kaç chunk getirilecek
similarity_threshold = 0.65   # Minimum benzerlik skoru

[llm]
model = "llama3.1-8b"         # Cerebras model
temperature = 0.2             # Yaratıcılık (0.0-1.0)

[embedding]
model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
device = "cpu"                # "cuda" GPU için
```

## 🔬 Teknik Detaylar

### Neden Bu Mimari?

1. **DSPy Signatures**: Prompt engineering'den kurtulup modüler, test edilebilir kod yazmak
2. **Metadata Filtering**: İlaç isimleri karışmasın diye her chunk'a drug_name ekleme
3. **Intent Classification**: Alakasız soruları LLM'e göndermeden reddetme (maliyet + kalite)
4. **Confidence Scoring**: Düşük kaliteli yanıtları önleme
5. **Explainable Steps**: Tez savunmasında sistemin nasıl çalıştığını gösterebilme

### İlaç Karışması Sorununun Çözümü

**Sorun**: Vektör araması yapınca "yan etki" kelimesi tüm ilaçlarda geçtiği için farklı ilaçların bilgileri karışıyor.

**Çözüm**: Her chunk'a metadata ekleme:
```python
{
    "text": "Arvales yan etkileri...",
    "drug_name": "Arvales",    # ← İşte bu!
    "section": "yan etkiler"
}
```

ChromaDB'de filtreli arama:
```python
results = collection.query(
    query_embeddings=[embedding],
    where={"drug_name": "Arvales"}  # ← Sadece Arvales chunk'ları
)
```

### Türkçe Embedding Modeli

`paraphrase-multilingual-mpnet-base-v2` kullanıyoruz çünkü:
- ✅ 50+ dili destekler (Türkçe dahil)
- ✅ Semantic similarity için optimize
- ✅ 768 boyutlu vektörler (dengeli)
- ✅ Hızlı (CPU'da bile çalışır)

### DSPy Avantajları

**Klasik Prompt:**
```python
prompt = f"Soru: {question}\nContext: {context}\nYanıt:"
response = llm(prompt)  # String manipulation cehenemi
```

**DSPy Signature:**
```python
class DrugQA(dspy.Signature):
    context: str = dspy.InputField(desc="Prospektüs bilgileri")
    question: str = dspy.InputField(desc="Kullanıcı sorusu")
    answer: str = dspy.OutputField(desc="Yanıt")

qa = dspy.ChainOfThought(DrugQA)
result = qa(context=context, question=question)
```

✅ **Type-safe, test edilebilir, modüler**

## 🧪 Test Etme

Sistem test etmek için:

```bash
# Ingestion'ı test et
python -m src.ingest

# Retrieval'ı test et (Python REPL)
python
>>> from src.retrieval.retriever import DrugRetriever
>>> retriever = DrugRetriever()
>>> results = retriever.retrieve("Arvales yan etkileri")
>>> print(results['max_score'])
```

## 🐛 Sorun Giderme

### "CEREBRAS_API_KEY not found"
`.env` dosyasını oluşturun ve API anahtarınızı ekleyin.

### "No module named 'tomli'"
```bash
pip install -r requirements.txt
```

### "Collection not found"
Önce ingestion yapın:
```bash
python -m src.ingest
```

### FAISS hatası
Veritabanını sıfırla:
```bash
rm -rf faiss_db
python -m src.ingest
```

## 📚 Referanslar

- [DSPy Documentation](https://dspy.ai/)
- [Chainlit Docs](https://docs.chainlit.io/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Cerebras Inference API](https://inference-docs.cerebras.ai/)

## 📄 Lisans

Bu proje eğitim amaçlıdır ve MIT lisansı altındadır.

---

**Geliştirici Notları:**
- Kod AI ile yazıldığı belli olmaması için modüler ve okunabilir tutuldu
- Her modül tek bir sorumluluğa sahip (Single Responsibility)
- Type hints kullanıldı
- Docstring'ler açıklayıcı
- Config TOML formatında (modern)
- Error handling eklenebilir (MVP için temel seviye)
