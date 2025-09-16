#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенные тестовые запросы для улучшенной системы классификации
"""

from enhanced_query_router import QueryType

# Расширенный набор тестовых запросов для достижения 90% точности
ENHANCED_TEST_QUERIES = [
    # АВТОМОБИЛЬНЫЕ ВОПРОСЫ (расширенные)
    ("Что такое ABS?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни что такое турбонаддув", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое гибридный двигатель?", QueryType.AUTOMOTIVE_QUESTION),
    ("Расскажи про ESP систему", QueryType.AUTOMOTIVE_QUESTION),
    ("Что означает ASR в автомобиле?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни принцип работы катализатора", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое сажевый фильтр?", QueryType.AUTOMOTIVE_QUESTION),
    ("Как работает вариатор?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое DSG коробка?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни разницу между 4WD и AWD", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое подвеска МакФерсон?", QueryType.AUTOMOTIVE_QUESTION),
    ("Как работает система стабилизации?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое мультимедиа система?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни что такое КАСКО", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое техосмотр автомобиля?", QueryType.AUTOMOTIVE_QUESTION),
    
    # СРАВНЕНИЯ (расширенные)
    ("Что лучше: бензин или газ?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни автомат и механику", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: BMW или Mercedes?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни дизель и бензин", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: передний или полный привод?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни седан и хэтчбек", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: новый или подержанный автомобиль?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни Toyota и Honda", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: кроссовер или внедорожник?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни электромобиль и гибрид", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: вариатор или автомат?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни KIA и Hyundai", QueryType.AUTOMOTIVE_COMPARISON),
    
    # РЕКОМЕНДАЦИИ (расширенные)
    ("Порекомендуй авто для семьи", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Какой автомобиль выбрать для города?", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй экономичный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Рекомендуй машину для начинающего водителя", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Какой автомобиль лучше для дальних поездок?", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй надежную машину до 1.5 млн", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Рекомендуй автомобиль для большой семьи", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Какую машину выбрать для работы?", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй спортивный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Рекомендуй внедорожник для дачи", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Какой автомобиль лучше для зимы?", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй машину с автоматом", QueryType.AUTOMOTIVE_RECOMMENDATION),
    
    # ПОМОЩЬ (расширенные)
    ("Как найти подходящий автомобиль?", QueryType.AUTOMOTIVE_HELP),
    ("Помоги выбрать машину", QueryType.AUTOMOTIVE_HELP),
    ("Что нужно знать при покупке авто?", QueryType.AUTOMOTIVE_HELP),
    ("Как правильно выбрать автомобиль?", QueryType.AUTOMOTIVE_HELP),
    ("Помоги найти хорошую машину", QueryType.AUTOMOTIVE_HELP),
    ("Что важно при выборе автомобиля?", QueryType.AUTOMOTIVE_HELP),
    ("Как не ошибиться при покупке машины?", QueryType.AUTOMOTIVE_HELP),
    ("Помоги с выбором первого автомобиля", QueryType.AUTOMOTIVE_HELP),
    ("Что проверить при покупке подержанного авто?", QueryType.AUTOMOTIVE_HELP),
    ("Как выбрать автомобиль по бюджету?", QueryType.AUTOMOTIVE_HELP),
    ("Помоги определиться с типом кузова", QueryType.AUTOMOTIVE_HELP),
    ("Что учесть при выборе марки автомобиля?", QueryType.AUTOMOTIVE_HELP),
    
    # СИСТЕМНАЯ ПОМОЩЬ (расширенные)
    ("Что ты умеешь?", QueryType.SYSTEM_HELP),
    ("Расскажи о своих возможностях", QueryType.SYSTEM_HELP),
    ("Кто ты?", QueryType.SYSTEM_HELP),
    ("Какие у тебя функции?", QueryType.SYSTEM_HELP),
    ("Что ты можешь делать?", QueryType.SYSTEM_HELP),
    ("Расскажи что умеешь", QueryType.SYSTEM_HELP),
    ("Покажи свои возможности", QueryType.SYSTEM_HELP),
    ("Какие команды ты понимаешь?", QueryType.SYSTEM_HELP),
    ("Что ты знаешь об автомобилях?", QueryType.SYSTEM_HELP),
    ("Расскажи о себе", QueryType.SYSTEM_HELP),
    ("Как ты работаешь?", QueryType.SYSTEM_HELP),
    ("Помощь", QueryType.SYSTEM_HELP),
    
    # ОБЩИЙ ЧАТ (расширенные)
    ("Привет", QueryType.GENERAL_CHAT),
    ("Как дела?", QueryType.GENERAL_CHAT),
    ("Спасибо", QueryType.GENERAL_CHAT),
    ("Здравствуйте", QueryType.GENERAL_CHAT),
    ("Добрый день", QueryType.GENERAL_CHAT),
    ("Добрый вечер", QueryType.GENERAL_CHAT),
    ("Доброе утро", QueryType.GENERAL_CHAT),
    ("Как поживаете?", QueryType.GENERAL_CHAT),
    ("Чем занимаетесь?", QueryType.GENERAL_CHAT),
    ("Хорошо", QueryType.GENERAL_CHAT),
    ("Отлично", QueryType.GENERAL_CHAT),
    ("Пока", QueryType.GENERAL_CHAT),
    ("До свидания", QueryType.GENERAL_CHAT),
    
    # ПОИСК АВТОМОБИЛЕЙ (расширенные)
    ("Найди красный BMW", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи машины до 2 млн", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу седан 2020 года", QueryType.AUTOMOTIVE_SEARCH),
    ("Найди белый Mercedes", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи внедорожники", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу хэтчбек с автоматом", QueryType.AUTOMOTIVE_SEARCH),
    ("Найди машины до 1 млн рублей", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи Toyota Camry", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу дизельные автомобили", QueryType.AUTOMOTIVE_SEARCH),
    ("Найди машины с полным приводом", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи кроссоверы 2021 года", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу экономичные автомобили", QueryType.AUTOMOTIVE_SEARCH),
    ("Найди машины в Москве", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи автомобили с пробегом до 50000 км", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу машины с одной владелицей", QueryType.AUTOMOTIVE_SEARCH),
    
    # КРЕДИТНЫЕ РАСЧЕТЫ (расширенные)
    ("Рассчитай кредит на 2 млн", QueryType.CREDIT_CALCULATION),
    ("Кредитный калькулятор", QueryType.CREDIT_CALCULATION),
    ("Посчитай ежемесячный платеж", QueryType.CREDIT_CALCULATION),
    ("Рассчитай кредит на автомобиль", QueryType.CREDIT_CALCULATION),
    ("Сколько будет переплата по кредиту?", QueryType.CREDIT_CALCULATION),
    ("Калькулятор автокредита", QueryType.CREDIT_CALCULATION),
    ("Рассчитай ипотеку на машину", QueryType.CREDIT_CALCULATION),
    ("Посчитай ставку по кредиту", QueryType.CREDIT_CALCULATION),
    ("Рассчитай первоначальный взнос", QueryType.CREDIT_CALCULATION),
    ("Сколько нужно на первоначальный взнос?", QueryType.CREDIT_CALCULATION),
    ("Рассчитай срок кредита", QueryType.CREDIT_CALCULATION),
    ("Посчитай общую стоимость кредита", QueryType.CREDIT_CALCULATION),
    
    # ДОПОЛНИТЕЛЬНЫЕ ТИПЫ ВОПРОСОВ
    
    # Технические характеристики
    ("Какая мощность у двигателя 2.0?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что означает объем двигателя 1.6?", QueryType.AUTOMOTIVE_QUESTION),
    ("Какой расход топлива у гибрида?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое крутящий момент?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни что такое компрессия", QueryType.AUTOMOTIVE_QUESTION),
    
    # Безопасность
    ("Что такое система экстренного торможения?", QueryType.AUTOMOTIVE_QUESTION),
    ("Как работает система контроля слепых зон?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое адаптивный круиз-контроль?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни систему помощи при парковке", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое система мониторинга давления в шинах?", QueryType.AUTOMOTIVE_QUESTION),
    
    # Комфорт и удобство
    ("Что такое климат-контроль?", QueryType.AUTOMOTIVE_QUESTION),
    ("Как работает система подогрева сидений?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое память настроек сидений?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни систему голосового управления", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое проекционный дисплей?", QueryType.AUTOMOTIVE_QUESTION),
    
    # Экология
    ("Что такое экологический класс Евро-6?", QueryType.AUTOMOTIVE_QUESTION),
    ("Как работает система рекуперации энергии?", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое каталитический нейтрализатор?", QueryType.AUTOMOTIVE_QUESTION),
    ("Объясни принцип работы электромобиля", QueryType.AUTOMOTIVE_QUESTION),
    ("Что такое plug-in гибрид?", QueryType.AUTOMOTIVE_QUESTION),
    
    # Сложные сравнения
    ("Что лучше для города: седан или хэтчбек?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни бензиновый и дизельный двигатель по экономичности", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: передний привод или полный привод для зимы?", QueryType.AUTOMOTIVE_COMPARISON),
    ("Сравни автомат и вариатор по надежности", QueryType.AUTOMOTIVE_COMPARISON),
    ("Что лучше: новый автомобиль за 1.5 млн или подержанный за 2 млн?", QueryType.AUTOMOTIVE_COMPARISON),
    
    # Специфические рекомендации
    ("Рекомендуй автомобиль для молодой семьи с ребенком", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй машину для пожилого человека", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Какой автомобиль выбрать для такси?", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Рекомендуй машину для частых поездок по трассе", QueryType.AUTOMOTIVE_RECOMMENDATION),
    ("Посоветуй автомобиль для активного отдыха", QueryType.AUTOMOTIVE_RECOMMENDATION),
    
    # Сложные поисковые запросы
    ("Найди красный BMW X5 с пробегом до 100000 км", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи белые седаны 2019-2021 года до 2.5 млн", QueryType.AUTOMOTIVE_SEARCH),
    ("Ищу дизельные внедорожники с автоматом", QueryType.AUTOMOTIVE_SEARCH),
    ("Найди машины с одной владелицей в Санкт-Петербурге", QueryType.AUTOMOTIVE_SEARCH),
    ("Покажи гибридные автомобили до 3 млн рублей", QueryType.AUTOMOTIVE_SEARCH),
]

def get_enhanced_test_queries():
    """Возвращает расширенный набор тестовых запросов"""
    return ENHANCED_TEST_QUERIES

def get_queries_by_type(query_type: QueryType):
    """Возвращает запросы определенного типа"""
    return [(query, expected_type) for query, expected_type in ENHANCED_TEST_QUERIES if expected_type == query_type]

def get_statistics():
    """Возвращает статистику по типам запросов"""
    stats = {}
    for query, query_type in ENHANCED_TEST_QUERIES:
        if query_type not in stats:
            stats[query_type] = 0
        stats[query_type] += 1
    return stats

if __name__ == "__main__":
    stats = get_statistics()
    print("📊 СТАТИСТИКА ТЕСТОВЫХ ЗАПРОСОВ:")
    for query_type, count in stats.items():
        print(f"{query_type.value}: {count} запросов")
    
    print(f"\n📈 ОБЩЕЕ КОЛИЧЕСТВО: {len(ENHANCED_TEST_QUERIES)} запросов")
