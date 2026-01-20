# Pharma-Navigator — Yüksek Lisans Projesi

Pharma-Navigator, ilaç prospektüslerini (Kullanma Talimatları) hızlı ve doğru biçimde analiz etmek için "Metadata-based Routing" yaklaşımını kullanan bir sohbet sistemidir. Bu çalışma, klasik RAG (Retrieval-Augmented Generation) mimarisine alternatif olarak, veriyi vektör veritabanına gömmek yerine, döküman fihristinden yola çıkarak ilgili sayfaları seçen bir **Router-Brain** tasarımı sunar.

---

## İçindekiler
- Özet (Abstract)
- Amaç ve Katkılar
- Bilimsel Arka Plan
- Mimari Genel Bakış
- Veri Seti ve Etik
- Kurulum
- Hızlı Başlangıç
- Deneylerin Yeniden Üretimi
- Değerlendirme ve Metrikler
- Proje Yapısı
- Test ve Doğrulama
- Atıf (Citation)
- Lisans

---

## Özet (Abstract)
Geleneksel RAG sistemleri, vektör veritabanı kurulumu ve embedding süreçleri nedeniyle yavaş, maliyetli ve bağlam kaybına açıktır. Pharma-Navigator, prospektüslerin hiyerarşik yapısını TONL (Transformed Object Notation for LLMs) formatına dönüştürerek, fihrist (master index) üzerinden doğru sayfaları seçer ve yalnızca bu sayfaları LLM'e bağlam olarak verir. Böylece yanıt süresi kısalır, token tüketimi azalır ve prospektüs sadakati korunur.

## Amaç ve Katkılar
- Klasik RAG'a kıyasla daha **hızlı** ve **maliyet-etkin** bir çözüm tasarlamak.
- Prospektüs hiyerarşisini koruyarak **bağlam kaybını önlemek**.
- TONL veri formatı ile **%90’a varan token tasarrufu** sağlamak.
- Gerçek kullanıcı sorularına **anti-halüsinasyon** prensibiyle cevaplamak.

## Bilimsel Arka Plan
- Karşılaştırma tabanı: Geleneksel RAG (vektör DB + embedding + chunking) vs. Metadata Routing.
- Hipotez: Metadata Routing, prospektüs gibi hiyerarşik dökümanlarda daha hızlı ve doğru sonuç verir.
- Metodoloji: Aynı sorgu setiyle iki yaklaşımın yanıt süresi, doğruluk ve maliyet karşılaştırması.

## Mimari Genel Bakış
"Router-Brain" stratejisi iki aşamadan oluşur:
- Router: `data/master_index.tonl` dosyasını tarar, ilgili ilaç ID’sini ve sayfa numaralarını belirler. (bkz. [src/core/router.py](src/core/router.py))
- Brain: Sadece seçilen sayfaları `data/processed_tonl/{drug}.tonl` dosyasından okur ve LLM ile cevap üretir. (bkz. [src/core/brain.py](src/core/brain.py))

Detaylı mimari ve örnek TONL yapısı için PRD’yi inceleyin: [prd.md](prd.md)

## Veri Seti ve Etik
- Kaynak: Kamuya açık veya kurumsal erişime sahip Türkçe prospektüs PDF’leri.
- Dönüşüm: Marker-pdf ile PDF → JSON; ardından TONL formatına dönüştürme.
- Etik: Kişisel veri içermez. Akademik kullanım için referans ve kaynak korunur.
- Depolama: Ham PDF’ler `data/pdfs/` altında tutulur (gitignore ile izleme dışında). TONL ve JSON dosyaları yalnızca örnekler için repoya eklenebilir.

## Kurulum
```bash
# Projeyi klonla
git clone <repo-url>
cd sohbetet

# Sanal ortam (Linux/Mac)
python -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Ortam değişkenleri (.env)
# Bu dosyayı el ile oluşturun ve aşağıdaki anahtarları ekleyin:
# CEREBRAS_API_KEY=<your_key>
# GOOGLE_API_KEY=<your_key>
```

Gereksinimler: Python 3.10+, `cerebras_cloud_sdk`, `google-generativeai`, `dspy-ai`, `chainlit`.

## Hızlı Başlangıç
```bash
# TONL üretimi (JSON → TONL)
python src/converters/json_to_tonl.py

# Master index üretimi
python src/converters/index_maker.py

# Chainlit uygulamasını başlat
chainlit run app.py -w
# Tarayıcı: http://localhost:8000
```

## Deneylerin Yeniden Üretimi
1. PDF’leri `data/{ilaç_adı}/` klasörlerine yerleştirin ve Marker-pdf ile JSON’a dönüştürün.
2. TONL üretimi için `src/converters/json_to_tonl.py` scriptini çalıştırın.
3. Master fihristi `src/converters/index_maker.py` ile oluşturun.
4. Router-Brain mimarisi ile örnek sorguları test edin:
   ```bash
   python test_navigator.py
   ```
5. Zaman ölçümü (örnek): Komut çalıştırma sürelerini kaydedin veya uygulama içinde sorgu başına toplam yanıt süresini ölçün.

## Değerlendirme ve Metrikler
- Yanıt Süresi: Router (<2s), TONL I/O (<0.5s), Brain (<3s), toplam (<5s) hedef.
- Doğruluk: Prospektüs sadakati (%100) ve sayfa seçim doğruluğu (%95+ hedef).
- Maliyet: Token tüketimi ve API çağrı maliyetleri (Cerebras + Gemini) karşılaştırması.

## Proje Yapısı
```
app.py                       # Chainlit ana uygulaması
prd.md                       # Ürün gereksinim dokümanı
requirements.txt             # Bağımlılıklar

data/
  master_index.tonl          # Router referans fihrist
  processed_tonl/            # TONL çıktıları
  pdfs/                      # Ham PDF (izleme dışı)

src/
  core/
    router.py                # DSPy Router
    brain.py                 # LLM Brain
  converters/
    json_to_tonl.py          # JSON → TONL dönüştürücü
    index_maker.py           # Master index üretici
```

## Test ve Doğrulama
- Hızlı test: [test_navigator.py](test_navigator.py)
- Çalıştırma:
  ```bash
  python test_navigator.py
  ```
- Test, Router ve Brain akışını uçtan uca doğrular ve örnek bir sorgu için cevap üretir.

## Atıf (Citation)
Aşağıdaki BibTeX girdisini düzenleyerek kendi bilgilerinizle kullanabilirsiniz:
```bibtex
@mastersthesis{PharmaNavigator2026,
  title={Pharma-Navigator: Metadata-based Routing for Drug Prospectuses},
  author={<Adınız Soyadınız>},
  school={<Üniversite Adı>},
  year={2026},
  address={<Şehir, Ülke>},
  type={Master's Thesis},
}
```

## Lisans
MIT. Ayrıntılar için proje kök dizinindeki lisans dosyasına bakınız (eklenecek).
