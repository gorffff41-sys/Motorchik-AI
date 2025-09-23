import json

from modules.classifiers.query_processor import UniversalQueryProcessor


def print_result(title: str, result: dict, max_items: int = 5):
    print("=" * 80)
    print(f"Q: {title}")
    if not isinstance(result, dict):
        print("Result type:", type(result))
        print(result)
        return
    print("Type:", result.get('type'))
    print("Message:", (result.get('message') or result.get('response') or '')[:500])
    entities = result.get('entities') or {}
    print("Entities:", json.dumps(entities, ensure_ascii=False))
    cars = result.get('cars') or []
    print("Cars found:", len(cars))
    for c in cars[:max_items]:
        mark = c.get('mark') or c.get('brand')
        model = c.get('model')
        year = c.get('manufacture_year') or c.get('year')
        price = c.get('price')
        city = c.get('city')
        color = c.get('color')
        print(f"- {mark} {model}, {year}, {price} ₽, {city}, {color}")


def main():
    qp = UniversalQueryProcessor()
    tests = [
        "найди машину от 160 л.с.",
        "машины 160-200 л.с.",
        "найди авто с пробегом до 50 тыс км",
        "какие машины есть от 160 л.с.",
        "какие машины есть 160-200 л.с.",
        "красная и синяя",
        "быстрый автомобиль",
        "дорогой кроссовер",
        "спорткар",
        "бмв",
    ]

    for q in tests:
        try:
            res = qp.process(q, entities={}, user_id='offline_demo', offset=0, limit=20, show_cars=True)
        except Exception as e:
            res = {"type": "error", "response": f"Exception: {e}", "cars": [], "entities": {}}
        print_result(q, res)


if __name__ == "__main__":
    main()



