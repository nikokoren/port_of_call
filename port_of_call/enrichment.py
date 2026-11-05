"""Optional, cached free sources. No enrichment request is on the HTTP response path.

Wikidata structured facts are CC0. Portnet is Fintraffic CC BY 4.0. Failed or
ambiguous matches remain unknown; names are never used as vessel identifiers.
"""
import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
import aiohttp
from .facts import imo, text
from .model import HARBORS, epoch, iso, mmsi

log = logging.getLogger('port_of_call.enrichment')
WIKI = 'https://www.wikidata.org/w/api.php'
HEADERS = {'User-Agent': 'PortOfCall/0.1 (https://github.com/nikokoren/port_of_call)',
           'Digitraffic-User': 'PortOfCall/0.1', 'Accept-Encoding': 'gzip'}
PORT_CODES = {'helsinki': 'FIHEL', 'turku': 'FITKU', 'rauma': 'FIRAU', 'rotterdam': 'NLRTM',
              'antwerp': 'BEANR', 'hamburg': 'DEHAM', 'bremerhaven': 'DEBRV', 'felixstowe': 'GBFXT',
              'southampton': 'GBSOU', 'los-angeles-long-beach': 'USLAX', 'new-york-new-jersey': 'USNYC',
              'savannah': 'USSAV', 'houston': 'USHOU', 'seattle': 'USSEA', 'charleston': 'USCHS',
              'singapore': 'SGSIN', 'shanghai-yangshan': 'CNSHA', 'busan-new-port': 'KRPUS'}
# These factual aliases are deliberately small and exact. Composite harbor areas
# do not imply that both component ports share a UN/LOCODE.
LOCAL_PORTS = {code: dict(code=code, name=HARBORS[key]['name'], position=HARBORS[key]['center'])
               for key, code in PORT_CODES.items() if key not in ('shanghai-yangshan', 'busan-new-port')}
LOCAL_PORTS.update(USLAX=dict(code='USLAX', name='Los Angeles', position=[-118.25, 33.74]),
                   USLGB=dict(code='USLGB', name='Long Beach', position=[-118.21, 33.75]))
ALIASES = {k: v for code, v in LOCAL_PORTS.items() for k in (code, v['name'].upper())}
ALIASES.update({name.upper(): LOCAL_PORTS[code] for name, code in
                [('Helsinki', 'FIHEL'), ('Turku', 'FITKU'), ('Rauma', 'FIRAU'), ('Rotterdam', 'NLRTM'),
                 ('Antwerp', 'BEANR'), ('Hamburg', 'DEHAM'), ('Singapore', 'SGSIN'), ('Seattle', 'USSEA')]})


def port_key(raw):
    key = re.sub(r'\s+', '', raw.upper()) if isinstance(raw, str) else ''
    return key if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}', key) else None


def cached(store, key, now):
    row = store.db.execute('SELECT ts,payload FROM enrichment WHERE key=? AND expires>?', (key, now)).fetchone()
    return (row[0], json.loads(row[1])) if row else None


def save_cache(store, key, payload, now, ttl):
    store.db.execute('INSERT OR REPLACE INTO enrichment VALUES (?,?,?,?)', (key, now, now+ttl, json.dumps(payload)))
    store.commit()


def resolve_port(store, raw, now):
    if not raw: return None
    local = ALIASES.get(raw.strip().upper()) or LOCAL_PORTS.get(port_key(raw))
    if local: return {**local, 'source': 'Reviewed harbor catalog'}
    key = port_key(raw)
    hit = cached(store, 'port:'+key, now) if key else None
    return hit[1] if hit else None


def enrich_card(store, port, focus, now):
    destination = focus.get('destination')
    focus['destination_port'] = resolve_port(store, destination['value'], now) if destination else None
    hit = cached(store, 'ship:'+focus['imo'], now) if focus.get('imo') else None
    if hit and hit[1]: focus['enrichment'] = {**hit[1], 'fetched_at': iso(hit[0])}
    code = PORT_CODES.get(port['id'])
    observed = epoch(focus['reported_at'])
    for ts, payload in store.db.execute('SELECT ts,payload FROM port_calls WHERE ts>? AND ts<=? ORDER BY ts DESC', (now-7*86400, now)):
        call = json.loads(payload)
        if call['port'] != code: continue
        if focus.get('imo') and call.get('imo') and focus['imo'] != call['imo']: continue
        if not ((focus.get('imo') and focus['imo'] == call.get('imo')) or focus['mmsi'] == call.get('mmsi')): continue
        if not call.get('ata') or not 0 <= observed-call['ata'] < 7*86400: continue
        if call.get('atd') and call['atd'] <= observed: continue
        # Use an actual current visit record; never turn a planned or old call into origin.
        previous = call.get('previous')
        if previous:
            resolved = resolve_port(store, previous, now)
            focus['origin'] = dict(value=resolved['name'] if resolved else previous, code=previous,
                                   source='Fintraffic / Digitraffic Portnet', reported_at=iso(ts),
                                   url='https://www.digitraffic.fi/en/marine-traffic/',
                                   license='https://creativecommons.org/licenses/by/4.0/')
        break


def claim_values(entity, prop):
    values = []
    for claim in entity.get('claims', {}).get(prop, []):
        # Ended roles and deprecated statements must not look like current operators.
        if claim.get('rank') == 'deprecated' or 'P582' in claim.get('qualifiers', {}): continue
        snak = claim.get('mainsnak', {})
        if snak.get('snaktype') == 'value' and 'datavalue' in snak: values.append(snak['datavalue']['value'])
    return values


def label(entity):
    return text(entity.get('labels', {}).get('en', {}).get('value'))


class Enricher:
    def __init__(self, store, provider, *, clock=time.time):
        self.store, self.provider, self.clock = store, provider, clock
        self.queue = asyncio.Queue(maxsize=128)
        self.pending = set()
        self.last_request = 0

    def enqueue(self, focus):
        if not focus: return
        keys = []
        if focus.get('imo'): keys.append(('ship', focus['imo']))
        for raw in [focus.get('destination', {}).get('value') if focus.get('destination') else None,
                    focus.get('origin', {}).get('code') if focus.get('origin') else None]:
            code = port_key(raw)
            if code and code not in LOCAL_PORTS: keys.append(('port', code))
        for kind, key in keys:
            token = kind+':'+key
            if token not in self.pending and not cached(self.store, token, self.clock()) and not self.queue.full():
                self.queue.put_nowait((kind, key)); self.pending.add(token)

    async def request(self, session, **params):
        # Hard, persisted shared budget. This API has no paid fallback or billing account.
        day = datetime.fromtimestamp(self.clock(), timezone.utc).strftime('%Y-%m-%d')
        budget_key = 'wikidata_daily_budget'
        state = json.loads(self.store.state(budget_key) or '{}')
        count = state.get('count', 0) if state.get('day') == day else 0
        if count >= 500: raise ValueError('Daily free enrichment budget exhausted')
        await asyncio.sleep(max(0, 1-(time.monotonic()-self.last_request)))
        self.store.state(budget_key, json.dumps(dict(day=day, count=count+1)))
        self.last_request = time.monotonic()
        async with session.get(WIKI, params={'format': 'json', **params}, headers=HEADERS) as response:
            response.raise_for_status()
            body = bytearray()
            async for chunk in response.content.iter_chunked(65536):
                body.extend(chunk)
                if len(body) > 2_000_000: raise ValueError('Oversized enrichment')
            data = json.loads(body)
            if 'error' in data: raise ValueError('Enrichment API error')
            return data

    async def lookup(self, session, prop, identifier):
        data = await self.request(session, action='query', list='search', srsearch=f'haswbstatement:{prop}={identifier}',
                                  srnamespace=0, srlimit=4)
        hits = data.get('query', {}).get('search', [])
        if not hits or len(hits) > 3: return None
        ids = [h['title'] for h in hits if re.fullmatch(r'Q\d+', h.get('title', ''))]
        if not ids: return None
        entities = (await self.request(session, action='wbgetentities', ids='|'.join(ids), props='claims|labels', languages='en')).get('entities', {})
        exact = [e for e in entities.values() if identifier in claim_values(e, prop)]
        return exact[0] if len(exact) == 1 else None

    async def refresh(self, session, kind, key):
        token, now = kind+':'+key, self.clock()
        hit = cached(self.store, token, now)
        if hit: return hit[1]
        try:
            entity = await self.lookup(session, 'P458' if kind == 'ship' else 'P1937', key)
            result = None
            if entity:
                source = dict(source='Wikidata', url='https://www.wikidata.org/wiki/'+entity['id'], license='https://creativecommons.org/publicdomain/zero/1.0/')
                if kind == 'port':
                    coords = claim_values(entity, 'P625')
                    valid = [c for c in coords if c.get('globe') == 'http://www.wikidata.org/entity/Q2'
                             and isinstance(c.get('longitude'), (int, float)) and isinstance(c.get('latitude'), (int, float))
                             and -180 <= c['longitude'] <= 180 and -85 <= c['latitude'] <= 85]
                    if len(valid) == 1 and label(entity):
                        result = dict(code=key, name=label(entity), position=[valid[0]['longitude'], valid[0]['latitude']], **source)
                else:
                    refs = {}
                    for prop, title in [('P289', 'Class'), ('P176', 'Builder'), ('P137', 'Operator')]:
                        vals = claim_values(entity, prop)
                        ids = list(dict.fromkeys(v['id'] for v in vals if isinstance(v, dict) and re.fullmatch(r'Q\d+', v.get('id', ''))))
                        if len(ids) == 1: refs[title] = ids[0]
                    labels = {}
                    if refs:
                        labels = (await self.request(session, action='wbgetentities', ids='|'.join(set(refs.values())), props='labels', languages='en')).get('entities', {})
                    facts = [dict(label=title, value=label(labels.get(qid, {}))) for title, qid in refs.items() if label(labels.get(qid, {}))]
                    dates = claim_values(entity, 'P729')
                    if len(dates) == 1 and isinstance(dates[0], dict) and dates[0].get('precision', 0) >= 9:
                        match = re.match(r'^\+(\d{4})-', dates[0].get('time', ''))
                        if match and 1700 <= int(match[1]) <= datetime.fromtimestamp(now, timezone.utc).year:
                            facts.append(dict(label='In service', value=match[1]))
                    if facts: result = dict(facts=facts[:4], **source)
            save_cache(self.store, token, result, now, 30*86400 if result else 7*86400)
            return result
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
            log.warning('optional_enrichment_unavailable kind=%s error=%s', kind, type(exc).__name__)
            save_cache(self.store, token, None, now, 3600)
            return None

    async def portnet(self, session):
        now = self.clock()
        if self.provider != 'digitraffic' or now-float(self.store.state('portnet_attempt') or 0) < 3600: return
        self.store.state('portnet_attempt', now)
        try:
            async with session.get('https://meri.digitraffic.fi/api/port-call/v1/port-calls', headers=HEADERS) as response:
                response.raise_for_status()
                data = await response.json()
            # Retain only identifiers, ports and actual event times. No agents, masters,
            # customs records, contact details or full raw response are persisted.
            for call in data['portCalls']:
                try:
                    ts = epoch(call['portCallTimestamp'])
                    if not 0 <= now-ts < 7*86400 or call.get('portToVisit') not in ('FIHEL', 'FITKU', 'FIRAU'): continue
                    areas = call.get('portAreaDetails', [])
                    arrivals = [epoch(a['ata']) for a in areas if a.get('ata')]
                    departures = [epoch(a['atd']) for a in areas if a.get('atd')]
                    clean = dict(port=call['portToVisit'], previous=port_key(call.get('prevPort')),
                                 imo=imo(call.get('imoLloyds')), mmsi=mmsi(call.get('mmsi')),
                                 ata=min(arrivals) if arrivals else None, atd=max(departures) if departures else None)
                    self.store.db.execute('INSERT OR REPLACE INTO port_calls VALUES (?,?,?)', (str(call['portCallId']), ts, json.dumps(clean)))
                except (ValueError, KeyError, TypeError): continue
            self.store.commit()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
            log.warning('optional_portnet_unavailable error=%s', type(exc).__name__)

    async def run(self):
        async with aiohttp.ClientSession(trust_env=True, timeout=aiohttp.ClientTimeout(total=30, sock_connect=10)) as session:
            while True:
                await self.portnet(session)
                try: kind, key = await asyncio.wait_for(self.queue.get(), timeout=60)
                except asyncio.TimeoutError: continue
                try: await self.refresh(session, kind, key)
                finally:
                    self.pending.discard(kind+':'+key)
                    self.queue.task_done()
