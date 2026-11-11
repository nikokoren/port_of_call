"""Exact bundled names, with binary search to avoid a large per-Worker dictionary."""
from functools import lru_cache
from ._locode_data import DATA, COUNTRIES, SNAPSHOT_DATE


@lru_cache(maxsize=256)
def _row(code):
    if not isinstance(code, str) or len(code) != 5: return None
    lo, hi = 0, len(DATA)
    while lo < hi:
        mid = (lo+hi)//2
        newline = DATA.rfind('\n', lo, mid)
        start = lo if newline < 0 else newline+1
        end = DATA.find('\n', start)
        key = DATA[start:start+5]
        if key == code:
            _, qid, name = DATA[start:end].split('\t', 2)
            return qid, name
        if key < code: lo = end+1
        else: hi = start
    return None


def lookup(code):
    row = _row(code)
    if row is None: return None
    qid, name = row
    return dict(code=code, name=name, country=COUNTRIES.get(code[:2]),
        source='Wikidata CC0 location reference', url='https://www.wikidata.org/wiki/'+qid,
        license='https://creativecommons.org/publicdomain/zero/1.0/', reference_date=SNAPSHOT_DATE)
