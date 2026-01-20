import dspy
import os
import re
from dotenv import load_dotenv

load_dotenv()

class PharmaBrain:
    def __init__(self):
        # Cevabı da Cerebras'ın en güçlü modeliyle (Llama 3.3 70B) üretiyoruz
        self.lm = dspy.LM('cerebras/llama-3.3-70b', api_key=os.getenv("CEREBRAS_API_KEY"))
        # DSPy global ayarlarında bu modeli kullanmasını sağlıyoruz
        dspy.configure(lm=self.lm)

    def get_tonl_context(self, drug_id, pages):
        """TONL dosyasından sadece seçilen sayfaları çeker."""
        # Router'dan gelen 'DRUG[ID]' formatındaki ID'yi dosya adıyla uyumlu hale getir
        clean_id = drug_id.replace("DRUG[", "").replace("]", "")
        file_path = f"data/processed_tonl/{clean_id}.tonl"
        
        if not os.path.exists(file_path):
            return f"Hata: {file_path} dosyası bulunamadı."
        
        context = []
        is_relevant = False
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Sayfa başlangıcını yakala (P[0]: gibi)
                page_match = re.search(r'P\[(\d+)\]:', line)
                if page_match:
                    page_num = int(page_match.group(1))
                    is_relevant = page_num in pages
                
                # İlaç başlığını veya seçili sayfaları bağlama ekle
                if is_relevant or line.startswith("DRUG["):
                    context.append(line)
        return "".join(context)

    def answer(self, query, context):
        """Bağlamı kullanarak Cerebras üzerinden cevap üretir."""
        prompt = f"""Sen uzman bir eczacısın. Aşağıdaki ilaç prospektüsü verilerine dayanarak kullanıcı sorusunu teknik ve anlaşılır bir dille cevapla.
        Verilerde olmayan bilgiyi uydurma.

        BAĞLAM (TONL VERİSİ):
        {context}

        SORU:
        {query}
        """
        # DSPy LM üzerinden doğrudan çağrı yapıyoruz
        response = self.lm(prompt)
        # Cevap genellikle bir liste döner, ilk elemanı alıyoruz
        return response[0] if isinstance(response, list) else response