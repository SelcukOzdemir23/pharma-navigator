"""Chainlit app for Pharma Navigator.

İlaç prospektüsü bilgi asistanı - RAG tabanlı soru-cevap sistemi.

Usage:
    chainlit run src/app.py
"""

import os
from typing import Optional, Dict
import tomli
import dspy
import chainlit as cl
from chainlit import Step

from src.models.intent import classify_intent
from src.models.qa import generate_answer
from src.retrieval.retriever import DrugRetriever


# Load config
def load_config(config_path: str = "config.toml") -> dict:
    """TOML config dosyasını yükler."""
    with open(config_path, 'rb') as f:
        return tomli.load(f)


# Global config
CONFIG = load_config()

# Initialize DSPy LM
def init_dspy_lm() -> dspy.LM:
    """Cerebras LM'i initialize eder."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError(
            "CEREBRAS_API_KEY environment variable not set. "
            "Please set it in your .env file."
        )
    
    # Cerebras API (OpenAI compatible endpoint)
    lm = dspy.LM(
        model=CONFIG['llm']['model'],
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1",
        temperature=CONFIG['llm']['temperature'],
        max_tokens=CONFIG['llm']['max_tokens']
    )
    
    return lm


# Initialize retriever
def init_retriever() -> DrugRetriever:
    """DrugRetriever'ı initialize eder."""
    return DrugRetriever(
        db_path=CONFIG['database']['path'],
        collection_name=CONFIG['database']['collection_name'],
        embedding_model=CONFIG['embedding']['model']
    )


# Global instances
LM = None
RETRIEVER = None


@cl.on_chat_start
async def start():
    """Chat başladığında çalışır."""
    global LM, RETRIEVER
    
    # Initialize components
    async with cl.Step(name="🔧 Sistem Başlatılıyor") as step:
        try:
            # Initialize LM
            step.output = "Language model bağlanıyor..."
            LM = init_dspy_lm()
            dspy.configure(lm=LM)
            
            # Initialize retriever
            step.output = "Veritabanı yükleniyor..."
            RETRIEVER = init_retriever()
            
            # Get stats
            stats = RETRIEVER.get_collection_stats()
            
            step.output = (
                f"✅ Sistem hazır!\n\n"
                f"📊 **Veritabanı İstatistikleri:**\n"
                f"- Toplam chunk: {stats['total_chunks']}\n"
                f"- İlaç sayısı: {len(stats['unique_drugs'])}\n"
                f"- İlaçlar: {', '.join(stats['unique_drugs'])}"
            )
            
        except Exception as e:
            step.output = f"❌ Başlatma hatası: {str(e)}"
            step.is_error = True
            raise
    
    # Welcome message
    await cl.Message(
        content=(
            f"# {CONFIG['ui']['title']}\n\n"
            f"{CONFIG['ui']['description']}\n\n"
            f"**Mevcut ilaçlar:** {', '.join(stats['unique_drugs'])}\n\n"
            f"💡 Örnek sorular:\n"
            f"- Arvales'in yan etkileri nelerdir?\n"
            f"- Cipralex nasıl kullanılır?\n"
            f"- Janumet'i kimler kullanamaz?\n\n"
            f"Sorunuzu yazabilirsiniz! 👇"
        )
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Kullanıcı mesajı geldiğinde çalışır."""
    user_query = message.content
    
    # Step 1: Intent Classification
    async with cl.Step(name="🎯 Intent Sınıflandırma") as intent_step:
        intent_step.output = f"Soru analiz ediliyor: '{user_query[:50]}...'"
        
        intent_result = classify_intent(user_query, LM)
        
        if not intent_result['is_drug_related']:
            # Refusal
            intent_step.output = (
                f"❌ İlaç dışı soru tespit edildi.\n\n"
                f"**Gerekçe:** {intent_result['reasoning']}"
            )
            
            await cl.Message(
                content=intent_result['refusal_message']
            ).send()
            return
        
        # Success
        drug_names = intent_result['drug_names']
        intent_step.output = (
            f"✅ İlaç sorusu tespit edildi\n\n"
            f"**Tespit edilen ilaçlar:** {', '.join(drug_names) if drug_names else 'Genel soru'}\n"
            f"**Gerekçe:** {intent_result['reasoning']}"
        )
    
    # Step 2: Retrieval
    async with cl.Step(name="🔍 Bilgi Arama") as retrieval_step:
        retrieval_step.output = "Prospektüsler taranıyor..."
        
        retrieval_result = RETRIEVER.retrieve(
            query=user_query,
            drug_names=drug_names if drug_names else None,
            top_k=CONFIG['retrieval']['top_k'],
            similarity_threshold=CONFIG['retrieval']['similarity_threshold']
        )
        
        chunks = retrieval_result['chunks']
        max_score = retrieval_result['max_score']
        
        if not chunks:
            retrieval_step.output = (
                f"⚠️ Yeterli bilgi bulunamadı\n\n"
                f"**Max benzerlik skoru:** {max_score:.2f}\n"
                f"**Threshold:** {CONFIG['retrieval']['similarity_threshold']}"
            )
            retrieval_step.is_error = True
            
            await cl.Message(
                content=(
                    "Üzgünüm, bu soruya yanıt verebilecek yeterli bilgi bulamadım. "
                    "Lütfen sorunuzu farklı kelimelerle ifade etmeyi deneyin veya "
                    "daha spesifik bir ilaç adı belirtin."
                )
            ).send()
            return
        
        # Format retrieval results
        sources_text = "\n".join([
            f"{i+1}. **{c['metadata']['drug_name']}** - {c['metadata']['section']} "
            f"(skor: {c['score']:.2f})"
            for i, c in enumerate(chunks)
        ])
        
        retrieval_step.output = (
            f"✅ {len(chunks)} ilgili bölüm bulundu\n\n"
            f"**Kaynaklar:**\n{sources_text}\n\n"
            f"**Max benzerlik:** {max_score:.2f}"
        )
        
        # Format context for LLM
        context = RETRIEVER.format_context(chunks)
    
    # Step 3: Answer Generation
    async with cl.Step(name="💬 Yanıt Oluşturma") as answer_step:
        answer_step.output = "Yanıt üretiliyor..."
        
        answer_result = generate_answer(
            question=user_query,
            context=context,
            lm=LM,
            check_confidence=True
        )
        
        if not answer_result['is_sufficient']:
            answer_step.output = "⚠️ Context yeterli değil"
            answer_step.is_error = True
            
            await cl.Message(
                content=answer_result['answer']
            ).send()
            return
        
        answer_step.output = (
            f"✅ Yanıt üretildi\n\n"
            f"**Güven seviyesi:** {answer_result['confidence']}\n"
            f"**Kullanılan bölümler:** {', '.join(answer_result['sources'])}"
        )
    
    # Final response
    final_message = answer_result['answer']
    
    # Add sources if enabled
    if CONFIG['ui']['show_sources'] and chunks:
        final_message += "\n\n---\n\n**📚 Kaynaklar:**\n"
        for i, chunk in enumerate(chunks[:3], 1):  # Top 3
            meta = chunk['metadata']
            final_message += (
                f"\n{i}. **{meta['drug_name']}** - {meta['section']} "
                f"({meta['source_file']})"
            )
    
    # Add confidence if enabled
    if CONFIG['ui']['show_confidence']:
        confidence_emoji = {
            'yüksek': '🟢',
            'orta': '🟡',
            'düşük': '🔴'
        }
        emoji = confidence_emoji.get(answer_result['confidence'], '⚪')
        final_message += f"\n\n{emoji} *Güven: {answer_result['confidence']}*"
    
    await cl.Message(content=final_message).send()


@cl.on_chat_end
def end():
    """Chat bittiğinde çalışır."""
    print("Chat session ended")


if __name__ == "__main__":
    # For debugging
    print("Use: chainlit run src/app.py -w")
