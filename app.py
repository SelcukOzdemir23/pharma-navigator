import chainlit as cl
from src.core.router import NavigatorRouter
from src.core.brain import PharmaBrain

# Sistem bileşenlerini başlatıyoruz
router = NavigatorRouter()
brain = PharmaBrain()

@cl.on_chat_start
async def start():
    await cl.Message(content="👋 Merhaba! Pharma-Navigator'a hoş geldiniz. İlaç prospektüsleri hakkında merak ettiğiniz her şeyi sorabilirsiniz.").send()

@cl.on_message
async def main(message: cl.Message):
    # 1. Adım: Kullanıcıya bekleme mesajı göster (Adım adım takip için)
    status_msg = cl.Message(content="🔍 İlgili bölümler taranıyor...")
    await status_msg.send()

    # 2. Adım: Router ile yönlendirme yap
    route_info = router.route(message.content)
    
    status_msg.content = f"✅ {route_info['drug']} bulundu. Sayfa {route_info['pages']} analiz ediliyor..."
    await status_msg.update()

    # 3. Adım: İlgili bağlamı çek ve Brain'e sor
    context = brain.get_tonl_context(route_info['drug'], route_info['pages'])
    answer = brain.answer(message.content, context)

    # 4. Adım: Final cevabı gönder
    await cl.Message(content=answer).send()