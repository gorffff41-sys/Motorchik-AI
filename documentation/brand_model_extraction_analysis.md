# АНАЛИЗ МОДУЛЕЙ ИЗВЛЕЧЕНИЯ МАРКИ И МОДЕЛИ
================================================================================

📊 СТАТИСТИКА:
   Всего модулей: 15
   Модулей с извлечением марки/модели: 12
   Модулей с запросами к БД: 13

📁 ДЕТАЛЬНЫЙ АНАЛИЗ ПО МОДУЛЯМ:
--------------------------------------------------------------------------------

📄 test_queries_improved.py:
   🔍 Функции извлечения марки/модели:
     - Строка 12: def extract_brand_model_improved(query: str) -> tuple:
     - Строка 12: def extract_brand_model_improved(query: str) -> tuple:
     - Строка 12: def extract_brand_model_improved(query: str) -> tuple:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 372: def search_cars_by_criteria_improved(research_tool, query_analysis: dict) -> list:
     - Строка 383: SELECT * FROM car
     - Строка 385: SELECT * FROM used_car
     ... и еще 3

📄 yandex_car_research_with_db.py:
   🔍 Функции извлечения марки/модели:
     - Строка 239: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 239: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 239: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 53: def search_cars_in_db(self, brand: str, model: str) -> List[Dict]:
     - Строка 266: def search_wikipedia_improved(self, query: str) -> Dict:
     - Строка 356: def search_drom_ru_improved(self, brand: str, model: str) -> Dict:
     ... и еще 14
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: get_db_connection, search_cars_in_db, get_car_options_from_db, get_car_details_from_db, search_wikipedia_improved, search_drom_ru_improved, search_auto_ru_improved, research_car_with_db

📄 yandex_car_research.py:
   🔍 Функции извлечения марки/модели:
     - Строка 66: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 66: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 66: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 97: def search_wikipedia_improved(self, query: str) -> Dict:
     - Строка 189: def search_drom_ru_improved(self, brand: str, model: str) -> Dict:
     - Строка 290: def search_auto_ru_improved(self, brand: str, model: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: search_wikipedia_improved, search_drom_ru_improved, search_auto_ru_improved, research_car_with_yandex

📄 yandex_car_research_simple.py:
   🔍 Функции извлечения марки/модели:
     - Строка 38: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 38: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 38: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 65: def search_wikipedia_improved(self, query: str) -> Dict:
     - Строка 155: def search_drom_ru_improved(self, brand: str, model: str) -> Dict:
     - Строка 254: def search_auto_ru_improved(self, brand: str, model: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: search_wikipedia_improved, search_drom_ru_improved, search_auto_ru_improved, research_car_simple

📄 nlp_processor.py:
   🔍 Функции извлечения марки/модели:
     - Строка 237: def extract_brand_from_text(text: str) -> Optional[str]:
     - Строка 314: def extract_model_from_text(text, brand=None):
     - Строка 210: brand = extract_brand_from_text(text)
     ... и еще 4
   🗄️ Запросы к БД:
     - Строка 57: def get_first_deep(val):
     - Строка 1261: def get_user_preferences(self, user_id: str) -> Dict[str, List[str]]:
     - Строка 1265: def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
     ... и еще 19
   🏷️ Методы извлечения: _load_models, _save_models, _extract_entities, _extract_price, retrain_models, get_model_performance, get_all_brands_cached, get_all_models_cached
   📊 Методы БД: _get_extended_training_data, get_user_preferences, get_user_history, get_recommendations, get_model_performance, get_all_brands_cached, get_all_models_cached, get_all_cities_cached, get_all_dealers_cached, get_all_fuel_types_cached, get_all_body_types_cached, get_all_transmissions_cached, get_all_drive_types_cached

📄 intelligent_query_processor.py:
   🗄️ Запросы к БД:
     - Строка 21: def get_first_deep(val):
     - Строка 930: def get_data_statistics(self) -> Dict[str, Any]:
     - Строка 1172: def get_car_db_schema(self) -> Dict:
     ... и еще 39
   🏷️ Методы извлечения: _check_model_loaded, handle_specific_model_query, get_model_info, get_model_options, is_option_suitable_for_model
   📊 Методы БД: get_data_statistics, get_car_db_schema, handle_search_query, get_model_info, get_model_options, get_fallback_response

📄 database.py:
   🗄️ Запросы к БД:
     - Строка 1699: def search_options_by_code(code: str) -> List[Dict[str, Any]]:
     - Строка 1868: def search_all_cars(
     - Строка 25: def get_db():
     ... и еще 101
   📊 Методы БД: get_simple_cache, get_context

📄 modules/classifiers/query_processor.py:
   🗄️ Запросы к БД:
     - Строка 179: def get_all_unique_field_values(field):
     - Строка 240: def get_all_unique_options():
     - Строка 569: def get_sort_key(car):
     ... и еще 24
   🏷️ Методы извлечения: extract_entities_from_text
   📊 Методы БД: get_context

📄 test_yandex_simple.py:
   🔍 Функции извлечения марки/модели:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: test_wikipedia_search, test_drom_ru_search, test_auto_ru_search

📄 test_car_research.py:
   🔍 Функции извлечения марки/модели:
     - Строка 27: def extract_brand_model(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 27: def extract_brand_model(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 27: def extract_brand_model(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 75: def search_wikipedia(self, query: str) -> Dict:
     - Строка 120: def search_google(self, query: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model
   📊 Методы БД: search_wikipedia, search_google, research_car

📄 test_car_research_advanced.py:
   🔍 Функции извлечения марки/модели:
     - Строка 32: def extract_brand_model_advanced(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 32: def extract_brand_model_advanced(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 32: def extract_brand_model_advanced(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 102: def search_wikipedia_advanced(self, query: str) -> Dict:
     - Строка 162: def search_google_real(self, query: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model_advanced
   📊 Методы БД: search_wikipedia_advanced, search_google_real, research_car_advanced

📄 test_car_research_final.py:
   🔍 Функции извлечения марки/модели:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 31: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 62: def search_wikipedia_improved(self, query: str) -> Dict:
     - Строка 131: def search_google_improved(self, query: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: search_wikipedia_improved, search_google_improved, research_car_final

📄 test_car_research_fixed.py:
   🔍 Функции извлечения марки/модели:
     - Строка 32: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 32: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     - Строка 32: def extract_brand_model_simple(self, query: str) -> Tuple[Optional[str], Optional[str]]:
     ... и еще 3
   🗄️ Запросы к БД:
     - Строка 63: def search_wikipedia_full_query(self, query: str) -> Dict:
     - Строка 129: def search_google_simulation(self, query: str) -> Dict:
   🏷️ Методы извлечения: extract_brand_model_simple
   📊 Методы БД: search_wikipedia_full_query, search_google_simulation, research_car_fixed

📄 test_simple_car_research.py:
   🔍 Функции извлечения марки/модели:
     - Строка 79: brand, model = research_tool.extract_brand_model_advanced(query)
     - Строка 79: brand, model = research_tool.extract_brand_model_advanced(query)

📄 test_queries_from_photo.py:
   🔍 Функции извлечения марки/модели:
     - Строка 44: brand, model = research_tool.extract_brand_model_simple(query)
     - Строка 44: brand, model = research_tool.extract_brand_model_simple(query)
   🗄️ Запросы к БД:
     - Строка 173: def search_cars_by_criteria(research_tool, query_analysis: dict) -> list:
     - Строка 184: SELECT * FROM car
     - Строка 186: SELECT * FROM used_car
     ... и еще 3

🔄 АНАЛИЗ ПОТОКОВ ДАННЫХ:
--------------------------------------------------------------------------------

✅ Модули с полным циклом (извлечение + БД):
   - test_queries_improved.py
   - yandex_car_research_with_db.py
   - yandex_car_research.py
   - yandex_car_research_simple.py
   - nlp_processor.py
   - test_car_research.py
   - test_car_research_advanced.py
   - test_car_research_final.py
   - test_car_research_fixed.py
   - test_queries_from_photo.py

💡 РЕКОМЕНДАЦИИ:
--------------------------------------------------------------------------------
✅ Найдены модули с полным циклом обработки
   Рекомендуется использовать их как основу