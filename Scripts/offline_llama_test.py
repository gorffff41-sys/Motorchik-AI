import json
from modules.classifiers.query_processor import UniversalQueryProcessor


def main():
    qp = UniversalQueryProcessor()
    tests = [
        "какие машины есть быстрые",
        "какие машины есть недорогие",
        "какие машины есть красные",
        "какие машины есть на 7 мест",
        "какие машины есть до 2 млн",
        "какие машины есть от 160 л.с.",  # должно уйти в БД (строгий фильтр)
    ]
    for q in tests:
        res = qp.process(q, entities={}, user_id='llama_offline', offset=0, limit=10, show_cars=True)
        print('='*80)
        print('Q:', q)
        print('Type:', res.get('type'))
        print('Message:', (res.get('message') or res.get('response') or '')[:400])
        print('Entities:', json.dumps(res.get('entities') or {}, ensure_ascii=False))
        cars = res.get('cars') or []
        print('Cars:', len(cars))
        for c in cars[:5]:
            print('-', c.get('mark'), c.get('model'), c.get('manufacture_year'), c.get('price'), c.get('city'))


if __name__ == '__main__':
    main()

