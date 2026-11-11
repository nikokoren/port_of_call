"""Build a compact, exact-name CC0 Wikidata reference from completed TSV exports.

Fetch both queries documented in docs/port-reference.md, then pass their files.
No UNECE directory or guessed coordinates are incorporated.
"""
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from port_of_call.destinations import ISO_COUNTRIES


def rows(path):
    with path.open() as source:
        header = next(source).strip().split('\t')
        if header != ['?item', '?code', '?name']: raise ValueError('Unexpected TSV header')
        for line in source:
            cells = line.rstrip('\n').split('\t')
            if len(cells) != 3: raise ValueError('Incomplete TSV export')
            qid = re.fullmatch(r'<https?://www.wikidata.org/entity/(Q\d+)>', cells[0])
            if not qid: raise ValueError('Unexpected entity URI')
            values = []
            for cell in cells[1:]:
                literal = cell[:-3] if cell.endswith('@en') else cell
                if not literal.startswith('"') or not literal.endswith('"'): raise ValueError('Invalid TSV literal')
                # QLever TSV preserves inner quote characters literally. Decode
                # escaped control/unicode characters without interpreting text.
                inner = literal[1:-1]
                values.append(re.sub(r'\\(?:[tbnrf"\\]|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})',
                    lambda m: ast.literal_eval('"'+m[0]+'"'), inner))
            if not all(isinstance(v, str) for v in values): raise ValueError('Non-string reference')
            yield qid[1], values[0].replace(' ', '').upper(), ' '.join(values[1].split())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--locations', type=Path, required=True)
    p.add_argument('--countries', type=Path, required=True)
    p.add_argument('--date', required=True, help='Date the source exports were retrieved')
    args = p.parse_args()
    locations, countries = defaultdict(set), defaultdict(set)
    for qid, code, name in rows(args.locations):
        if re.fullmatch('[A-Z]{2}[A-Z2-9]{3}', code) and code[:2] in ISO_COUNTRIES and name and not re.search(r'\b(airport|airfield|aerodrome|air base)\b', name, re.I):
            locations[code].add((qid, name))
    for qid, code, name in rows(args.countries):
        if code in ISO_COUNTRIES and name: countries[code].add((qid, name))
    # One exact entity per code; conflicting records are left for reviewed lookup.
    accepted = {code: next(iter(items)) for code, items in locations.items() if len(items) == 1}
    country_names = {code: next(iter(items))[1] for code, items in countries.items() if len(items) == 1}
    records = [code+'\t'+qid+'\t'+name+'\n' for code, (qid, name) in sorted(accepted.items())]
    chunks = [''.join(records[i:i+100]) for i in range(0, len(records), 100)]
    output = '"""Generated CC0 Wikidata location names; see docs/port-reference.md. Do not edit."""\n'
    output += 'SNAPSHOT_DATE = '+repr(args.date)+'\n'
    output += 'COUNT = '+str(len(accepted))+'\n'
    output += 'COUNTRIES = '+repr(dict(sorted(country_names.items())))+'\n'
    output += 'DATA = (\n'+''.join('    '+json.dumps(chunk, ensure_ascii=False)+'\n' for chunk in chunks)+')\n'
    (ROOT/'port_of_call/_locode_data.py').write_text(output)
    evidence = dict(snapshot_date=args.date, licence='https://creativecommons.org/publicdomain/zero/1.0/',
        locations_endpoint='https://qlever.dev/api/wikidata', countries_endpoint='https://query.wikidata.org/sparql',
        locations_query='SELECT ?item ?code ?name WHERE { ?item wdt:P1937 ?code; rdfs:label ?name. FILTER(LANG(?name) = "en") FILTER NOT EXISTS { ?item wdt:P31/wdt:P279* wd:Q62447 } }',
        countries_query='SELECT ?item ?code ?name WHERE { ?item wdt:P297 ?code; rdfs:label ?name. FILTER(LANG(?name) = "en") }',
        names=len(accepted), countries=len(country_names), ambiguous_location_codes=sum(len(v)>1 for v in locations.values()),
        source_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.locations, args.countries]},
        output_sha256=hashlib.sha256(output.encode()).hexdigest())
    (ROOT/'docs/port-reference-snapshot.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print('Built',len(accepted),'exact location names,',len(country_names),'countries;',len(output.encode()),'source bytes')


if __name__ == '__main__': main()
