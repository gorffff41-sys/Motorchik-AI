import sqlite3
DB_PATH = r'E:\Users\diman\OneDrive\Документы\Рабочий стол\2\хрень — копия\instance\cars.db'

# Этот модуль будет отвечать за поиск автомобилей в базе данных
# на основе фильтров, извлеченных из запроса.

class SearchModule:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def search(self, query: str):
        """
        Выполняет поиск автомобилей по запросу.
        Возвращает 5 новых и 5 б/у машин.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Новые авто
            cursor.execute("SELECT id, mark, model, manufacture_year, price, color, body_type, fuel_type FROM car LIMIT 5")
            new_rows = cursor.fetchall()
            new_cars = [
                {"id": row[0], "mark": row[1], "model": row[2], "year": row[3], "price": row[4], "color": row[5], "body_type": row[6], "fuel_type": row[7], "used": False} for row in new_rows
            ]
            # Б/у авто
            cursor.execute("SELECT id, mark, model, manufacture_year, price, color, body_type, fuel_type, mileage FROM used_car LIMIT 5")
            used_rows = cursor.fetchall()
            used_cars = [
                {"id": row[0], "mark": row[1], "model": row[2], "year": row[3], "price": row[4], "color": row[5], "body_type": row[6], "fuel_type": row[7], "mileage": row[8], "used": True} for row in used_rows
            ]
            conn.close()
        except Exception as e:
            return {"type": "error", "message": str(e)}

        cars = new_cars + used_cars
        return {
            "type": "car_list",
            "query": query,
            "count": len(cars),
            "cars": cars
        } 