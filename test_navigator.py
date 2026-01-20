from src.core.router import NavigatorRouter
from src.core.brain import PharmaBrain

def run_test():
    try:
        router = NavigatorRouter()
        brain = PharmaBrain()
        
        query = "Sutesgo yan etkileri nelerdir?"
        print(f"🤔 Soru: {query}")
        
        # 1. Router karar verir (Cerebras LPU)
        route_info = router.route(query)
        print(f"🚦 Router Kararı: {route_info}")
        
        # 2. Sadece ilgili sayfalar çekilir
        context = brain.get_tonl_context(route_info['drug'], route_info['pages'])
        
        # 3. Gemini 2.0 cevaplar
        answer = brain.answer(query, context)
        print(f"\n💡 Cevap:\n{answer}")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    run_test()