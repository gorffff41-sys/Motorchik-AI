#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light wrapper that uses UltimateEntityExtractorSimple and brand_synonyms to
extract, normalize and map entities into DB search parameters.
"""
from typing import Dict, Any, Optional
from ultimate_entity_extractor_simple import UltimateEntityExtractorSimple
from brand_synonyms import normalize_brand_extended, MODEL_SYNONYMS
import re

_extractor = UltimateEntityExtractorSimple()


def _normalize_model(m: Optional[str]) -> Optional[str]:
    if not m:
        return None
    m0 = str(m).strip()
    key = m0.lower()
    if key in MODEL_SYNONYMS:
        return MODEL_SYNONYMS[key]
    return m0.title()


def extract_and_normalize(query: str) -> Dict[str, Any]:
    """
    Return a dict ready to be passed as 'entities' / filters to DB search.
    Maps extractor keys to the search_all_cars parameters.
    """
    q = (query or "").strip()
    if not q:
        return {}

    raw = _extractor.extract_entities(q)

    out: Dict[str, Any] = {}

    # brand / model
    brand = raw.get('brand') or raw.get('mark')
    if brand:
        out['brand'] = normalize_brand_extended(brand)

    model = raw.get('model')
    if model:
        out['model'] = _normalize_model(model)

    # price / ranges - extractor may return price_from/price_to or price
    if 'price' in raw:
        out['price_from'] = raw.get('price')
        out['price_to'] = raw.get('price')
    if 'price_from' in raw:
        out['price_from'] = raw.get('price_from')
    if 'price_to' in raw:
        out['price_to'] = raw.get('price_to')

    # years
    if 'year' in raw:
        out['year_from'] = raw.get('year')
        out['year_to'] = raw.get('year')
    if 'year_from' in raw:
        out['year_from'] = raw.get('year_from')
    if 'year_to' in raw:
        out['year_to'] = raw.get('year_to')

    # basic car attrs
    if raw.get('fuel_type'):
        out['fuel_type'] = raw.get('fuel_type')
    if raw.get('transmission'):
        out['transmission'] = raw.get('transmission')
    if raw.get('body_type'):
        out['body_type'] = raw.get('body_type')
    if raw.get('drive_type'):
        out['drive_type'] = raw.get('drive_type')
    if raw.get('city'):
        out['city'] = raw.get('city')
    if raw.get('color'):
        out['color'] = raw.get('color')

    # mileage / doors / owners
    if raw.get('mileage'):
        # extractor may return exact or range; try common keys
        m = raw.get('mileage')
        try:
            out['mileage_exact'] = int(m)
        except Exception:
            pass
    if raw.get('mileage_from'):
        out['mileage_from'] = raw.get('mileage_from')
    if raw.get('mileage_to'):
        out['mileage_to'] = raw.get('mileage_to')
    if raw.get('doors'):
        out['doors'] = raw.get('doors')
    if raw.get('owners'):
        try:
            out['owners_count'] = int(raw.get('owners'))
        except Exception:
            out['owners_count'] = raw.get('owners')

    # options -> pass as option_description for DB search
    if raw.get('options'):
        # join options to a single search string
        opts = raw.get('options')
        if isinstance(opts, (list, tuple)):
            out['option_description'] = ' '.join([str(o) for o in opts])
        else:
            out['option_description'] = str(opts)

    # steering wheel, consumption, euro_class, size, condition
    if raw.get('steering_wheel'):
        out['steering_wheel'] = raw.get('steering_wheel')
    if raw.get('consumption'):
        out['fuel_efficiency'] = raw.get('consumption')
    if raw.get('euro_class'):
        out['euro_class'] = raw.get('euro_class')
    if raw.get('size'):
        out['size'] = raw.get('size')
    if raw.get('condition'):
        cond = raw.get('condition')
        # normalize common forms
        if isinstance(cond, str) and re.search(r'used|б\W?у|бу|подерж', cond, re.I):
            out['state'] = 'used'
        elif isinstance(cond, str) and re.search(r'new|нов', cond, re.I):
            out['state'] = 'new'
        else:
            out['state'] = cond

    # copy any extra recognized keys directly
    for k in ('power_from', 'power_to', 'engine_vol_from', 'engine_vol_to'):
        if k in raw:
            out[k] = raw[k]

    return out
