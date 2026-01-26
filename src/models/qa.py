"""Drug QA module using DSPy signatures."""

import dspy
from typing import Optional


class DrugQA(dspy.Signature):
    """İlaç prospektüsü bilgilerini kullanarak soruları yanıtlar.
    
    Retrieval edilen prospektüs bölümlerini kullanarak doğru,
    kaynaklı ve güvenilir yanıtlar üretir.
    """
    
    context: str = dspy.InputField(
        desc="İlaç prospektüsünden retrieval edilen ilgili bölümler"
    )
    
    question: str = dspy.InputField(
        desc="Kullanıcının ilaç hakkındaki sorusu"
    )
    
    answer: str = dspy.OutputField(
        desc="Prospektüs bilgilerine dayalı detaylı yanıt (Türkçe)"
    )
    
    confidence: str = dspy.OutputField(
        desc="Yanıtın güvenilirlik seviyesi: 'yüksek', 'orta', veya 'düşük'"
    )
    
    source_sections: str = dspy.OutputField(
        desc="Yanıtta kullanılan prospektüs bölümleri (virgülle ayrılmış)"
    )


class ConfidenceChecker(dspy.Signature):
    """Retrieval sonuçlarının soruya uygunluğunu değerlendirir."""
    
    question: str = dspy.InputField(desc="Kullanıcı sorusu")
    retrieved_context: str = dspy.InputField(desc="Bulunan prospektüs bilgileri")
    
    is_sufficient: bool = dspy.OutputField(
        desc="Context'in soruyu yanıtlamak için yeterli olup olmadığı"
    )
    
    reasoning: str = dspy.OutputField(
        desc="Karar gerekçesi"
    )


def generate_answer(
    question: str,
    context: str,
    lm: dspy.LM,
    check_confidence: bool = True
) -> dict:
    """İlaç sorusuna retrieval edilen bilgilerle yanıt üretir.
    
    Args:
        question: Kullanıcı sorusu
        context: Retrieval edilen prospektüs metinleri
        lm: DSPy language model
        check_confidence: Context yeterliliğini kontrol et
        
    Returns:
        {
            'answer': str,
            'confidence': str,
            'sources': list[str],
            'is_sufficient': bool
        }
    """
    with dspy.context(lm=lm):
        response = {
            'answer': '',
            'confidence': 'düşük',
            'sources': [],
            'is_sufficient': False
        }
        
        # Check if context is sufficient
        if check_confidence and context.strip():
            checker = dspy.Predict(ConfidenceChecker)
            check_result = checker(
                question=question,
                retrieved_context=context[:500]  # Sample for efficiency
            )
            response['is_sufficient'] = check_result.is_sufficient
            
            if not check_result.is_sufficient:
                response['answer'] = (
                    "Üzgünüm, bu soruya güvenilir bir yanıt verebilmek için "
                    "prospektüslerde yeterli bilgi bulamadım. Lütfen sorunuzu "
                    "farklı kelimelerle ifade etmeyi deneyin veya daha spesifik "
                    "bir ilaç adı belirtin."
                )
                return response
        
        # Generate answer using Chain of Thought
        qa_module = dspy.ChainOfThought(DrugQA)
        result = qa_module(context=context, question=question)
        
        # Parse sources
        sources = []
        if result.source_sections:
            sources = [
                s.strip() 
                for s in result.source_sections.split(",")
                if s.strip()
            ]
        
        response.update({
            'answer': result.answer,
            'confidence': result.confidence,
            'sources': sources,
            'is_sufficient': True
        })
        
        return response
