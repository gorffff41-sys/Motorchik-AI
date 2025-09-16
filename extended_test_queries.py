#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный набор из 150 тестовых запросов для системы фильтрации v3.0
"""

from enhanced_query_router_v4 import QueryType

# Расширенный набор из 150 тестовых запросов
EXTENDED_TEST_QUERIES = [
    # АВТОМОБИЛЬНЫЕ ВОПРОСЫ (30 запросов)
    ("Что такое ABS?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни что такое турбонаддув", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое гибридный двигатель?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Расскажи про ESP систему", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что означает ASR в автомобиле?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни принцип работы катализатора", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое сажевый фильтр?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Как работает вариатор?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое DSG коробка?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни разницу между 4WD и AWD", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое подвеска МакФерсон?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Как работает система стабилизации?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое мультимедиа система?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни что такое КАСКО", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое техосмотр автомобиля?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Какая мощность у двигателя 2.0?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что означает объем двигателя 1.6?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Какой расход топлива у гибрида?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое крутящий момент?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни что такое компрессия", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое система экстренного торможения?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Как работает система контроля слепых зон?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое адаптивный круиз-контроль?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни систему помощи при парковке", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое система мониторинга давления в шинах?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое климат-контроль?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Как работает система подогрева сидений?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое память настроек сидений?", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Объясни систему голосового управления", QueryType.AUTOMOTIVE_QUESTION, True),
    ("Что такое проекционный дисплей?", QueryType.AUTOMOTIVE_QUESTION, True),
    
    # СРАВНЕНИЯ (20 запросов)
    ("Что лучше: бензин или газ?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни автомат и механику", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: BMW или Mercedes?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни дизель и бензин", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: передний или полный привод?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни седан и хэтчбек", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: новый или подержанный автомобиль?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни Toyota и Honda", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: кроссовер или внедорожник?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни электромобиль и гибрид", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: вариатор или автомат?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни KIA и Hyundai", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше для города: седан или хэтчбек?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни бензиновый и дизельный двигатель по экономичности", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: передний привод или полный привод для зимы?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни автомат и вариатор по надежности", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: новый автомобиль за 1.5 млн или подержанный за 2 млн?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни Audi и BMW по комфорту", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Что лучше: дизель или бензин для города?", QueryType.AUTOMOTIVE_COMPARISON, True),
    ("Сравни японские и немецкие автомобили", QueryType.AUTOMOTIVE_COMPARISON, True),
    
    # РЕКОМЕНДАЦИИ (20 запросов)
    ("Порекомендуй авто для семьи", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какой автомобиль выбрать для города?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй экономичный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй машину для начинающего водителя", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какой автомобиль лучше для дальних поездок?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй надежную машину до 1.5 млн", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй автомобиль для большой семьи", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какую машину выбрать для работы?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй спортивный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй внедорожник для дачи", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какой автомобиль лучше для зимы?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй машину с автоматом", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй автомобиль для молодой семьи с ребенком", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй машину для пожилого человека", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какой автомобиль выбрать для такси?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй машину для частых поездок по трассе", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй автомобиль для активного отдыха", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Какую машину выбрать для бизнеса?", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Рекомендуй автомобиль для студента", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    ("Посоветуй машину для перевозки грузов", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
    
    # ПОМОЩЬ (15 запросов)
    ("Как найти подходящий автомобиль?", QueryType.AUTOMOTIVE_HELP, True),
    ("Помоги выбрать машину", QueryType.AUTOMOTIVE_HELP, True),
    ("Что нужно знать при покупке авто?", QueryType.AUTOMOTIVE_HELP, True),
    ("Как правильно выбрать автомобиль?", QueryType.AUTOMOTIVE_HELP, True),
    ("Помоги найти хорошую машину", QueryType.AUTOMOTIVE_HELP, True),
    ("Что важно при выборе автомобиля?", QueryType.AUTOMOTIVE_HELP, True),
    ("Как не ошибиться при покупке машины?", QueryType.AUTOMOTIVE_HELP, True),
    ("Помоги с выбором первого автомобиля", QueryType.AUTOMOTIVE_HELP, True),
    ("Что проверить при покупке подержанного авто?", QueryType.AUTOMOTIVE_HELP, True),
    ("Как выбрать автомобиль по бюджету?", QueryType.AUTOMOTIVE_HELP, True),
    ("Помоги определиться с типом кузова", QueryType.AUTOMOTIVE_HELP, True),
    ("Что учесть при выборе марки автомобиля?", QueryType.AUTOMOTIVE_HELP, True),
    ("Как выбрать надежный автомобиль?", QueryType.AUTOMOTIVE_HELP, True),
    ("Помоги с выбором двигателя", QueryType.AUTOMOTIVE_HELP, True),
    ("Что важно при покупке нового авто?", QueryType.AUTOMOTIVE_HELP, True),
    
    # СИСТЕМНАЯ ПОМОЩЬ (10 запросов)
    ("Что ты умеешь?", QueryType.SYSTEM_HELP, True),
    ("Расскажи о своих возможностях", QueryType.SYSTEM_HELP, True),
    ("Кто ты?", QueryType.SYSTEM_HELP, True),
    ("Какие у тебя функции?", QueryType.SYSTEM_HELP, True),
    ("Что ты можешь делать?", QueryType.SYSTEM_HELP, True),
    ("Расскажи что умеешь", QueryType.SYSTEM_HELP, True),
    ("Покажи свои возможности", QueryType.SYSTEM_HELP, True),
    ("Какие команды ты понимаешь?", QueryType.SYSTEM_HELP, True),
    ("Что ты знаешь об автомобилях?", QueryType.SYSTEM_HELP, True),
    ("Расскажи о себе", QueryType.SYSTEM_HELP, True),
    
    # БАЗОВОЕ ОБЩЕНИЕ (15 запросов)
    ("Привет", QueryType.GENERAL_CHAT, True),
    ("Как дела?", QueryType.GENERAL_CHAT, True),
    ("Спасибо", QueryType.GENERAL_CHAT, True),
    ("Здравствуйте", QueryType.GENERAL_CHAT, True),
    ("Добрый день", QueryType.GENERAL_CHAT, True),
    ("Добрый вечер", QueryType.GENERAL_CHAT, True),
    ("Доброе утро", QueryType.GENERAL_CHAT, True),
    ("Как поживаете?", QueryType.GENERAL_CHAT, True),
    ("Чем занимаетесь?", QueryType.GENERAL_CHAT, True),
    ("Хорошо", QueryType.GENERAL_CHAT, True),
    ("Отлично", QueryType.GENERAL_CHAT, True),
    ("Пока", QueryType.GENERAL_CHAT, True),
    ("До свидания", QueryType.GENERAL_CHAT, True),
    ("Хорошего дня", QueryType.GENERAL_CHAT, True),
    ("Удачи", QueryType.GENERAL_CHAT, True),
    
    # ПОИСК АВТОМОБИЛЕЙ (20 запросов)
    ("Найди красный BMW", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи машины до 2 млн", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу седан 2020 года", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди белый Mercedes", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи внедорожники", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу хэтчбек с автоматом", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди машины до 1 млн рублей", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи Toyota Camry", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу дизельные автомобили", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди машины с полным приводом", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи кроссоверы 2021 года", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу экономичные автомобили", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди машины в Москве", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи автомобили с пробегом до 50000 км", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу машины с одной владелицей", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди красный BMW X5 с пробегом до 100000 км", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи белые седаны 2019-2021 года до 2.5 млн", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Ищу дизельные внедорожники с автоматом", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Найди машины с одной владелицей в Санкт-Петербурге", QueryType.AUTOMOTIVE_SEARCH, True),
    ("Покажи гибридные автомобили до 3 млн рублей", QueryType.AUTOMOTIVE_SEARCH, True),
    
    # КРЕДИТНЫЕ РАСЧЕТЫ (10 запросов)
    ("Рассчитай кредит на 2 млн", QueryType.CREDIT_CALCULATION, True),
    ("Кредитный калькулятор", QueryType.CREDIT_CALCULATION, True),
    ("Посчитай ежемесячный платеж", QueryType.CREDIT_CALCULATION, True),
    ("Рассчитай кредит на автомобиль", QueryType.CREDIT_CALCULATION, True),
    ("Сколько будет переплата по кредиту?", QueryType.CREDIT_CALCULATION, True),
    ("Калькулятор автокредита", QueryType.CREDIT_CALCULATION, True),
    ("Рассчитай ипотеку на машину", QueryType.CREDIT_CALCULATION, True),
    ("Посчитай ставку по кредиту", QueryType.CREDIT_CALCULATION, True),
    ("Рассчитай первоначальный взнос", QueryType.CREDIT_CALCULATION, True),
    ("Сколько нужно на первоначальный взнос?", QueryType.CREDIT_CALCULATION, True),
    
    # НЕАВТОМОБИЛЬНЫЕ ЗАПРОСЫ (30 запросов) - должны отклоняться
    ("Расскажи про погоду", QueryType.NON_AUTOMOTIVE, False),
    ("Как приготовить борщ?", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое квантовая физика?", QueryType.NON_AUTOMOTIVE, False),
    ("Помоги с программированием", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи анекдот", QueryType.NON_AUTOMOTIVE, False),
    ("Как дела на работе?", QueryType.NON_AUTOMOTIVE, False),
    ("Что посмотреть в кино?", QueryType.NON_AUTOMOTIVE, False),
    ("Как выучить английский?", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про политику", QueryType.NON_AUTOMOTIVE, False),
    ("Как похудеть?", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое блокчейн?", QueryType.NON_AUTOMOTIVE, False),
    ("Помоги с математикой", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про историю", QueryType.NON_AUTOMOTIVE, False),
    ("Как инвестировать?", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое любовь?", QueryType.NON_AUTOMOTIVE, False),
    ("Как приготовить пиццу?", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про спорт", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое искусственный интеллект?", QueryType.NON_AUTOMOTIVE, False),
    ("Помоги с дизайном", QueryType.NON_AUTOMOTIVE, False),
    ("Как научиться рисовать?", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про музыку", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое философия?", QueryType.NON_AUTOMOTIVE, False),
    ("Помоги с психологией", QueryType.NON_AUTOMOTIVE, False),
    ("Как медитировать?", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про путешествия", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое экономика?", QueryType.NON_AUTOMOTIVE, False),
    ("Помоги с юриспруденцией", QueryType.NON_AUTOMOTIVE, False),
    ("Как играть на гитаре?", QueryType.NON_AUTOMOTIVE, False),
    ("Расскажи про медицину", QueryType.NON_AUTOMOTIVE, False),
    ("Что такое астрономия?", QueryType.NON_AUTOMOTIVE, False),
]

def get_extended_test_queries():
    """Возвращает расширенный набор из 150 тестовых запросов"""
    return EXTENDED_TEST_QUERIES

def get_queries_by_type(query_type: QueryType):
    """Возвращает запросы определенного типа"""
    return [(query, expected_type, should_process) for query, expected_type, should_process in EXTENDED_TEST_QUERIES if expected_type == query_type]

def get_statistics():
    """Возвращает статистику по типам запросов"""
    stats = {}
    for query, query_type, should_process in EXTENDED_TEST_QUERIES:
        if query_type not in stats:
            stats[query_type] = 0
        stats[query_type] += 1
    return stats

if __name__ == "__main__":
    stats = get_statistics()
    print("📊 СТАТИСТИКА РАСШИРЕННЫХ ТЕСТОВЫХ ЗАПРОСОВ:")
    for query_type, count in stats.items():
        print(f"{query_type.value}: {count} запросов")
    
    print(f"\n📈 ОБЩЕЕ КОЛИЧЕСТВО: {len(EXTENDED_TEST_QUERIES)} запросов")
