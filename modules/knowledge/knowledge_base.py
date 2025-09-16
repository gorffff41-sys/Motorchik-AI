import json

class KnowledgeBase:
    def __init__(self):
        # В будущем база знаний может загружаться из файла или СУБД
        self.db = {
            "abs": "Антиблокировочная система тормозов, которая предотвращает блокировку колес при резком торможении.",
            "гибрид": "Тип двигателя, сочетающий двигатель внутреннего сгорания (ДВС) и электромотор.",
            "оформление сделки": "Процесс включает в себя проверку документов, подписание договора купли-продажи и регистрацию автомобиля в ГИБДД."
        }

    def answer(self, query: str):
        """
        Ищет ответ на общий вопрос в базе знаний.
        """
        # Убеждаемся, что query - это строка
        if not isinstance(query, str):
            query = str(query)
        query_lower = query.lower()
        for key, value in self.db.items():
            if key in query_lower:
                return {
                    "type": "fact_response",
                    "source": "knowledge_base",
                    "answer": value
                }
        
        return None 