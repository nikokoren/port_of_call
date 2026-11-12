"""Refresh reviewed landmark candidates from CC0 Wikidata, without publishing them."""
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def get(base, **params):
    request = Request(base+'?'+urlencode(dict(format='json', **params)), headers={'User-Agent':'PortOfCall/0.1 (https://github.com/nikokoren/port_of_call)'})
    with urlopen(request, timeout=40) as response: return json.load(response)


def coordinate(entity):
    claims = [c for c in entity.get('claims', {}).get('P625', []) if c.get('rank') != 'deprecated']
    claims = [c for c in claims if c['mainsnak'].get('datavalue', {}).get('value', {}).get('globe') == 'http://www.wikidata.org/entity/Q2']
    claims = [c for c in claims if c.get('rank') == 'preferred'] or claims
    points = {tuple(round(c['mainsnak']['datavalue']['value'][k], 6) for k in ('longitude', 'latitude')) for c in claims}
    if len(points) != 1: raise ValueError('Missing or ambiguous Earth coordinate: '+entity.get('id', '?'))
    point = points.pop()
    if not all(math.isfinite(x) for x in point) or not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90:
        raise ValueError('Invalid landmark coordinate')
    return list(point)


def main():
    # Identities are reviewed explicitly: a Wikipedia redirect can resolve to a
    # whole port, company headquarters or a different town with the same name.
    from port_of_call.model import HARBORS
    catalog = json.loads((ROOT/'scripts/landmark_catalog.json').read_text())
    ids = sorted({r['qid'] for rows in catalog.values() for r in rows if r['decision'] == 'added'})
    entities = {}
    for offset in range(0, len(ids), 40):
        entities.update(get('https://www.wikidata.org/w/api.php', action='wbgetentities',
            ids='|'.join(ids[offset:offset+40]), props='claims')['entities'])
    landmarks = {}
    for port, rows in catalog.items():
        result = []
        for row in rows:
            if row['decision'] != 'added': continue
            point = coordinate(entities[row['qid']])
            center = HARBORS[port].get('focus') or HARBORS[port]['center']
            distance = 111*math.hypot((point[0]-center[0])*math.cos(math.radians(center[1])), point[1]-center[1])
            if distance > 75: raise ValueError('Review coordinate outside harbor vicinity: '+port+' / '+row['name'])
            result.append(dict(name=row['name'], position=point,
                source_url='https://www.wikidata.org/wiki/'+row['qid'],
                fact_ids=[f'{port}:{index}' for index in row['facts']]))
        landmarks[port] = result
    (ROOT/'var').mkdir(exist_ok=True)
    (ROOT/'var/landmark-candidates.json').write_text(json.dumps(landmarks,ensure_ascii=False,indent=2)+'\n')
    print('Wrote reviewed candidates; inspect coordinate changes before updating production references.')


if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT))
    main()
