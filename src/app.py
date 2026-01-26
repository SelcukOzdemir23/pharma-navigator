"""Gradio tabanlı Pharma Navigator (RAG) uygulaması."""

import os
from typing import Dict, List, Optional

import dspy
import gradio as gr
import tomli

from src.models.intent import classify_intent
from src.models.qa import generate_answer
from src.retrieval.retriever import DrugRetriever

# Silence litellm noisy logging/cache issues on Python 3.14
os.environ.setdefault("LITELLM_LOG", "false")
os.environ.setdefault("LITELLM_LOGGING_ENABLED", "false")
os.environ.setdefault("LITELLM_CACHE", "false")


def load_config(config_path: str = "config.toml") -> dict:
    """TOML config dosyasını yükler."""
    with open(config_path, "rb") as f:
        return tomli.load(f)


CONFIG = load_config()


def init_dspy_lm() -> dspy.LM:
    """Cerebras LM'i initialize eder."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise ValueError(
            "CEREBRAS_API_KEY environment variable not set. "
            "Please set it in your environment."
        )

    # litellm/Cerebras için sağlayıcıyı modele ekle
    model_name = CONFIG["llm"]["model"]
    if "/" not in model_name:
        model_name = f"cerebras/{model_name}"

    return dspy.LM(
        model=model_name,
        api_key=api_key,
        api_base="https://api.cerebras.ai/v1",
        temperature=CONFIG["llm"]["temperature"],
        max_tokens=CONFIG["llm"]["max_tokens"],
    )


def init_retriever() -> DrugRetriever:
    """DrugRetriever'ı initialize eder."""
    return DrugRetriever(
        db_path=CONFIG["database"]["path"],
        embedding_model=CONFIG["embedding"]["model"],
    )


LM: Optional[dspy.LM] = None
RETRIEVER: Optional[DrugRetriever] = None
STATS: Optional[Dict] = None


def detect_drugs_from_query(query: str, stats: Dict) -> List[str]:
    """Kullanıcı sorgusundan ilaç isimlerini case-insensitive yakala."""
    if not query:
        return []
    q = query.lower()
    detected = []
    for drug in stats.get("unique_drugs", []):
        if drug.lower() in q:
            detected.append(drug)
    return detected


def ensure_components_ready() -> Dict:
    """LM ve retriever'ı lazy olarak yükler."""
    global LM, RETRIEVER, STATS

    if LM is None or RETRIEVER is None:
        LM = init_dspy_lm()
        dspy.configure(lm=LM)
        RETRIEVER = init_retriever()
        STATS = RETRIEVER.get_collection_stats()

    if STATS is None:
        STATS = RETRIEVER.get_collection_stats()

    return STATS


def format_sources(chunks: List[Dict]) -> str:
    """Kaynak listesini biçimlendirir."""
    lines = []
    for i, chunk in enumerate(chunks[:3], 1):
        meta = chunk["metadata"]
        lines.append(f"{i}. {meta['drug_name']} - {meta['section']} ({meta['source_file']})")
    return "\n".join(lines)


def build_description(stats: Dict) -> str:
    """UI açıklamasını oluşturur."""
    drugs = ", ".join(stats.get("unique_drugs", [])) if stats else "Yükleniyor"
    return (
        f"{CONFIG['ui']['description']}\n\n"
        f"Mevcut ilaçlar: {drugs}\n"
        f"Örnek sorular: Arvales'in yan etkileri nelerdir?, Cipralex nasıl kullanılır?, Janumet'i kimler kullanamaz?"
    )


def handle_chat(message: str, history: Optional[List[Dict]] = None) -> str:
    """Gradio chat handler."""
    stats = ensure_components_ready()
    user_query = (message or "").strip()

    if not user_query:
        return "Lütfen bir soru yazın."

    intent_result = classify_intent(user_query, LM)
    if not intent_result["is_drug_related"]:
        return intent_result["refusal_message"]

    drug_names = intent_result["drug_names"]
    if not drug_names:
        drug_names = detect_drugs_from_query(user_query, stats)
    
    # Section filter: eğer intent modeli belirli bir bölüm tahmin ettiyse kullan
    section_filter = None
    if intent_result["inferred_section"] and intent_result["inferred_section"] != "genel":
        if intent_result["section_confidence"] in ["yüksek", "orta"]:
            section_filter = intent_result["inferred_section"]
    
    retrieval_result = RETRIEVER.retrieve(
        query=user_query,
        drug_names=drug_names if drug_names else None,
        top_k=CONFIG["retrieval"]["top_k"],
        similarity_threshold=CONFIG["retrieval"]["similarity_threshold"],
        section_filter=section_filter,
    )

    chunks = retrieval_result["chunks"]
    if not chunks:
        return (
            "Üzgünüm, bu soruya yanıt verebilecek yeterli bilgi bulamadım. "
            "Lütfen sorunuzu farklı kelimelerle ifade etmeyi deneyin veya daha spesifik bir ilaç adı belirtin."
        )

    context = RETRIEVER.format_context(chunks)
    
    # Debug: Show retrieved chunks for inspection
    chunks_debug = "**[Retrieval Debug - Raw Chunks]**\n"
    for i, chunk in enumerate(chunks, 1):
        chunks_debug += (
            f"\n{i}. Drug: {chunk['metadata']['drug_name']}\n"
            f"   Section: {chunk['metadata']['section']}\n"
            f"   Score: {chunk['score']:.3f}\n"
            f"   Text: {chunk['text'][:150]}...\n"
        )

    answer_result = generate_answer(
        question=user_query,
        context=context,
        lm=LM,
        check_confidence=True,
    )

    if not answer_result["is_sufficient"]:
        return answer_result["answer"]

    final_message = answer_result["answer"]

    if CONFIG["ui"].get("show_sources", True) and chunks:
        final_message += "\n\n---\n\nKaynaklar:\n" + format_sources(chunks)

    if CONFIG["ui"].get("show_confidence", True):
        confidence_emoji = {"yüksek": "🟢", "orta": "🟡", "düşük": "🔴"}
        emoji = confidence_emoji.get(answer_result["confidence"], "⚪")
        final_message += f"\n\n{emoji} Güven: {answer_result['confidence']}"

    # Optional lightweight trace of pipeline steps for transparency
    max_score = retrieval_result.get("max_score", 0)
    drugs_str = ", ".join(drug_names) if drug_names else "Genel"
    section_info = f"{intent_result['inferred_section']} ({intent_result['section_confidence']})" if section_filter else "Filtre yok"
    final_message += (
        "\n\n---\nAdımlar:\n"
        f"- Intent: ilaç sorusu ✓ (ilaçlar: {drugs_str}, bölüm: {section_info})\n"
        f"- Retrieval: {len(chunks)} bölüm, max skor {max_score:.2f}, threshold {CONFIG['retrieval']['similarity_threshold']}\n"
        f"- Yanıt: güven {answer_result['confidence']}"
    )

    # Add debug info for inspection
    final_message = chunks_debug + "\n\n" + final_message

    return final_message


def build_interface() -> gr.ChatInterface:
    stats = ensure_components_ready()
    description = build_description(stats)
    examples = [
        "Arvales'in yan etkileri nelerdir?",
        "Cipralex nasıl kullanılır?",
        "Janumet'i kimler kullanamaz?",
    ]

    return gr.ChatInterface(
        fn=handle_chat,
        title=CONFIG["ui"]["title"],
        description=description,
        examples=examples,
    )


if __name__ == "__main__":
    demo = build_interface()
    port = int(os.getenv("PORT", "8000"))
    share_flag = os.getenv("GRADIO_SHARE", "0").lower() in {"1", "true", "yes"}
    demo.launch(server_name="0.0.0.0", server_port=port, share=share_flag)
