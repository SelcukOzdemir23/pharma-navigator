"""Intent classification using DSPy signatures."""

import dspy
from typing import Literal


class IntentClassifier(dspy.Signature):
    """Kullanıcının sorusunun ilaçlarla ilgili olup olmadığını belirler.
    
    Bu classifier, sistemin sadece ilaç soruları yanıtlamasını sağlar.
    Alakasız sorular nazikçe reddedilir.
    """
    
    user_query: str = dspy.InputField(
        desc="Kullanıcının sorduğu soru (Türkçe)"
    )
    
    is_drug_related: bool = dspy.OutputField(
        desc="Sorunun ilaç/prospektüs hakkında olup olmadığı (true/false)"
    )
    
    detected_drug_names: str = dspy.OutputField(
        desc="Soruda geçen ilaç isimleri (virgülle ayrılmış, yoksa 'yok')"
    )
    
    reasoning: str = dspy.OutputField(
        desc="Karar verme süreci ve gerekçe"
    )


class RefusalHandler(dspy.Signature):
    """Ilaç dışı sorular için nazik reddetme mesajı üretir."""
    
    user_query: str = dspy.InputField(desc="Kullanıcının sorusu")
    
    refusal_message: str = dspy.OutputField(
        desc="Nazik ve yardımcı bir reddetme mesajı (Türkçe)"
    )


def classify_intent(query: str, lm: dspy.LM) -> dict:
    """Kullanıcı sorusunun intent'ini sınıflandırır.
    
    Args:
        query: Kullanıcı sorusu
        lm: DSPy language model
        
    Returns:
        {
            'is_drug_related': bool,
            'drug_names': list[str],
            'reasoning': str,
            'refusal_message': str | None
        }
    """
    with dspy.context(lm=lm):
        # Intent classification
        classifier = dspy.Predict(IntentClassifier)
        result = classifier(user_query=query)
        
        # Parse drug names
        drug_names = []
        if result.detected_drug_names and result.detected_drug_names.lower() != "yok":
            drug_names = [
                name.strip() 
                for name in result.detected_drug_names.split(",")
                if name.strip()
            ]
        
        response = {
            'is_drug_related': result.is_drug_related,
            'drug_names': drug_names,
            'reasoning': result.reasoning,
            'refusal_message': None
        }
        
        # Generate refusal message if needed
        if not result.is_drug_related:
            refusal_gen = dspy.Predict(RefusalHandler)
            refusal = refusal_gen(user_query=query)
            response['refusal_message'] = refusal.refusal_message
        
        return response
