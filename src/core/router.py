import dspy
import os
import re
from dotenv import load_dotenv

load_dotenv()

class PharmaRouterSignature(dspy.Signature):
    """Kullanıcı sorusuna göre fihristten ilgili ilacı ve sayfaları seçer."""
    master_index = dspy.InputField(desc="İlaç ID'leri ve sayfa başlıkları")
    query = dspy.InputField(desc="Kullanıcı sorusu")
    selected_drug = dspy.OutputField(desc="Fihristteki tam DRUG[ID]")
    relevant_pages = dspy.OutputField(desc="İlgili sayfa numaraları listesi. Örn: [0, 1]")

class NavigatorRouter:
    def __init__(self):
        # Cerebras'ın en güncel model ismini (llama-3.3-70b) kullanıyoruz
        # Eğer bu da hata verirse 'cerebras/llama3.1-8b' deneyebilirsin
        self.lm = dspy.LM('cerebras/llama-3.3-70b', api_key=os.getenv("CEREBRAS_API_KEY"))
        dspy.configure(lm=self.lm)
        self.predictor = dspy.Predict(PharmaRouterSignature)

    def route(self, query):
        with open("data/master_index.tonl", "r", encoding="utf-8") as f:
            index_content = f.read()
            
        prediction = self.predictor(master_index=index_content, query=query)
        
        # Sayfaları temizle
        pages_raw = prediction.relevant_pages
        if isinstance(pages_raw, str):
            pages = [int(s) for s in re.findall(r'\d+', pages_raw)]
        else:
            pages = pages_raw
            
        return {
            "drug": prediction.selected_drug,
            "pages": pages
        }