import json

from modules.classifiers.query_processor import UniversalQueryProcessor


def decide_routing(query: str, entities: dict) -> dict:
    ql = query.lower()

    def _present(key: str) -> bool:
        return entities.get(key) is not None

    def _pair_strict(a: str, b: str) -> bool:
        return _present(a) and _present(b)

    def _any_of(keys):
        return any(_present(k) for k in keys)

    is_command = any(w in ql for w in ['найди', 'покажи', 'подбери', 'подберите', 'подобери'])
    is_question_list = ('какие' in ql and 'есть' in ql and ('машин' in ql or 'авто' in ql))

    strict_pairs = [
        ('power_from', 'power_to'),
        ('mileage_from', 'mileage_to'),
        ('price_from', 'price_to'),
        ('year_from', 'year_to'),
        ('engine_vol_from', 'engine_vol_to'),
        ('acceleration_from', 'acceleration_to'),
        ('owners_from', 'owners_to'),
    ]
    has_strict_range = any(_pair_strict(a, b) for a, b in strict_pairs) or _present('power_exact') or _present('engine_vol_exact') or _present('owners_count')
    numeric_keys = [
        'power_from','power_to','power_exact','mileage_from','mileage_to','price_from','price_to','year_from','year_to',
        'engine_vol_from','engine_vol_to','engine_vol_exact','acceleration_from','acceleration_to','owners_from','owners_to','owners_count','seats'
    ]
    has_any_numeric = _any_of(numeric_keys)
    has_soft_numeric = has_any_numeric and not has_strict_range

    if is_command:
        route = 'DB:command'
    elif is_question_list and has_strict_range:
        route = 'DB:question+strict'
    elif is_question_list and has_soft_numeric:
        route = 'LLAMA:question+soft'
    elif has_any_numeric:
        route = 'DB:numeric'
    else:
        route = 'LLAMA:default'

    return {
        'is_command': is_command,
        'is_question_list': is_question_list,
        'has_any_numeric': has_any_numeric,
        'has_strict_range': has_strict_range,
        'has_soft_numeric': has_soft_numeric,
        'route': route,
    }


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
        "быстрая",
        "дорогой кроссовер",
        "дешевый седан",
        "спорткар",
        "бмв",
    ]

    print("OFFLINE TESTS (no HTTP API)\n" + "-" * 40)
    for q in tests:
        entities = qp.extract_entities_from_text(q)
        routing = decide_routing(q, entities)
        print(f"Q: {q}")
        print("Entities:", json.dumps(entities, ensure_ascii=False, sort_keys=True))
        print("Routing:", json.dumps(routing, ensure_ascii=False, sort_keys=True))
        print("-" * 40)


if __name__ == "__main__":
    main()



