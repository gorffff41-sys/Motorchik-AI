# Здесь будет логика для расчета кредита

class LoanCalculator:
    def calculate(self, car_id: int, params: dict):
        """
        Рассчитывает кредит для автомобиля.
        """
        # Демонстрационные данные, в будущем будут браться из БД
        car_price = 5000000 

        downpayment = params.get("downpayment", 0)
        term = params.get("term", 60) # месяцы
        rate = params.get("rate", 0.05) # годовая ставка

        if car_price <= downpayment:
            return {
                "type": "loan_calculation",
                "monthly_payment": 0,
                "message": "Первоначальный взнос покрывает стоимость автомобиля."
            }

        # Формула аннуитетного платежа
        monthly_rate = rate / 12
        credit_body = car_price - downpayment
        monthly_payment = credit_body * (monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
        
        return {
            "type": "loan_calculation",
            "car_id": car_id,
            "monthly_payment": round(monthly_payment, 2)
        } 