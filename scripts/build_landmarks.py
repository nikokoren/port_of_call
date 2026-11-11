"""Refresh a reviewed, small landmark catalog from CC0 Wikidata coordinates."""
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TITLES = {
 'helsinki': ['South Harbour, Helsinki', 'Suomenlinna'],
 'turku': ['Turku Castle', 'Ruissalo'], 'rauma': ['Port of Rauma', 'Kuuskajaskari'],
 'rotterdam': ['Maeslantkering', 'Beneluxtunnel'],
 'antwerp': ['Kieldrecht Lock', 'Berendrecht Lock'],
 'hamburg': ['Köhlbrand Bridge', 'St. Pauli Piers'],
 'bremerhaven': ['Kaiserschleuse', 'Simon Loschen Lighthouse'],
 'felixstowe': ['Landguard Fort', 'Harwich High Lighthouse'],
 'southampton': ['Hythe Pier, Railway and Ferry', 'Southampton Water'],
 'los-angeles-long-beach': ['Vincent Thomas Bridge', 'Long Beach International Gateway'],
 'new-york-new-jersey': ['Statue of Liberty', 'Verrazzano-Narrows Bridge'],
 'savannah': ['Talmadge Memorial Bridge', 'Old Fort Jackson'],
 'houston': ['Fred Hartman Bridge', 'San Jacinto Monument'],
 'seattle': ['Colman Dock', 'Smith Cove'],
 'charleston': ['Fort Sumter', 'Arthur Ravenel Jr. Bridge'],
 'singapore': ['Marina Bay Cruise Centre Singapore', 'Pasir Panjang Terminal'],
}


def get(base, **params):
    request = Request(base+'?'+urlencode(dict(format='json', **params)), headers={'User-Agent':'PortOfCall/0.1 (https://github.com/nikokoren/port_of_call)'})
    with urlopen(request, timeout=40) as response: return json.load(response)


def main():
    titles = [t for group in TITLES.values() for t in group]
    data = get('https://en.wikipedia.org/w/api.php', action='query', titles='|'.join(titles), redirects=1, prop='pageprops')
    aliases = {r['from']:r['to'] for r in data['query'].get('normalized', [])+data['query'].get('redirects', [])}
    pages = {p['title']:p.get('pageprops',{}).get('wikibase_item') for p in data['query']['pages'].values()}
    def qid(title):
        while title in aliases: title = aliases[title]
        return pages.get(title)
    entities = get('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(sorted({qid(t) for t in titles if qid(t)})), props='claims|labels', languages='en')['entities']
    landmarks = {}
    for port, group in TITLES.items():
        result = []
        for title in group:
            entity = entities.get(qid(title), {})
            coords = [c['mainsnak'].get('datavalue',{}).get('value',{}) for c in entity.get('claims',{}).get('P625',[]) if c.get('rank')!='deprecated']
            coords = [c for c in coords if c.get('globe')=='http://www.wikidata.org/entity/Q2' and 'longitude' in c and 'latitude' in c]
            if len(coords)!=1:
                print('REVIEW missing/ambiguous:', port, title, qid(title)); continue
            c = coords[0]
            result.append(dict(name=entity['labels']['en']['value'], position=[round(c['longitude'],6), round(c['latitude'],6)],
                source_url='https://www.wikidata.org/wiki/'+qid(title)))
        landmarks[port] = result
    (ROOT/'var/landmark-candidates.json').write_text(json.dumps(landmarks,ensure_ascii=False,indent=2)+'\n')
    print('Wrote candidates for human review; no production file is overwritten.')


if __name__=='__main__': main()
