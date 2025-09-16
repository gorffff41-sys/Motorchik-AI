# Отчет по уникальным значениям в базе данных

**Дата создания:** 29.06.2025  
**База данных:** instance/cars.db  
**Таблицы:** car, used_car

## Ключевые поля для фильтрации

### Бренды (mark)

**Таблица car (новые автомобили):**
- MAZDA, Москвич, SERES, AITO, Belgee, CHANGAN, Chery, Geely, Knewstar, Haval, SOLARIS, JAC, JAECOO, Jaecoo, OMODA, Tank, WEY

**Таблица used_car (б/у автомобили):**
- Nissan, Volkswagen, Li Auto, Lixiang, Mercedes-Benz, Geely, Land Rover, Audi, Jeep, DONGFENG, Lexus, Ford, Toyota, BYD, BMW, Voyah, GEELY, Tesla, KIA, Porsche, LiXiang, Hyundai, RAM, Zeekr, Kia, Mazda, Mitsubishi, Skoda, Tank, Renault, Haval, Chevrolet, Lada (ВАЗ), Peugeot, Alfa Romeo, Fiat, Chery, Honda, Opel, SsangYong, SKODA, AUDI, GAC, Volvo, Exeed, Subaru, NISSAN, GMC, kia, Dodge, MAZDA, Suzuki, JISHI, JEEP, HYUNDAI, OMODA, Omoda, Lada, VOLKSWAGEN, LADA, Citroen

### Типы кузова (body_type)

**Таблица car:**
- Кроссовер, Седан, Внедорожник, Лифтбэк, Купе-кроссовер, Универсал, Пикап, Хетчбэк, Минивэн

**Таблица used_car:**
- Внедорожник, Седан, Универсал, Хетчбэк, Пикап, Фургон, Микроавтобус, Минивэн, Купе

### Типы привода (driving_gear_type)

**Таблица car:**
- передний, полный

**Таблица used_car:**
- Полный, Задний, Передний

### Типы коробки передач (gear_box_type)

**Таблица car:**
- автомат, механика

**Таблица used_car:**
- Автомат, Механика

### Типы топлива (fuel_type)

**Таблица car:**
- 3 уникальных значения (не указаны в отчете)

**Таблица used_car:**
- Бензин, Гибрид, Электрический, Дизель

### Города (city)

**Обе таблицы:**
- 3 уникальных значения (не указаны в отчете)

### Годы производства (manufacture_year)

**Таблица car:**
- 5 уникальных значений (не указаны в отчете)

**Таблица used_car:**
- 21 уникальное значение (не указаны в отчете)

## Статистика

### Таблица car
- **Всего записей:** 100
- **Брендов:** 17
- **Моделей:** 66
- **Типов кузова:** 9
- **Типов привода:** 2
- **Типов коробки передач:** 2

### Таблица used_car
- **Всего записей:** 100
- **Брендов:** 61
- **Моделей:** 100
- **Типов кузова:** 9
- **Типов привода:** 3
- **Типов коробки передач:** 2
- **Типов топлива:** 4

## Важные замечания

1. **Различия в написании:** В таблицах есть различия в написании (например, "автомат" vs "Автомат", "передний" vs "Передний")

2. **Пустые поля:** Некоторые поля пустые (engine, door_qty, compl_level в таблице car; dealer_center, generation_id, modification_id в таблице used_car)

3. **Дублирование брендов:** Некоторые бренды написаны по-разному (например, "Geely" и "GEELY", "Kia" и "KIA")

4. **Полный отчет:** Детальный отчет с полными значениями сохранен в файле `unique_values_report_20250629_094544.json` 