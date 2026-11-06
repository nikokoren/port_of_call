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
from .facts import imo, text, radio_mid
from .model import HARBORS, epoch, iso, mmsi

log = logging.getLogger('port_of_call.enrichment')
WIKI = 'https://www.wikidata.org/w/api.php'
CACHE_VERSION = 'v2:'  # Country-aware records must not reuse older 30-day payloads.
HEADERS = {'User-Agent': 'PortOfCall/0.1 (https://github.com/nikokoren/port_of_call)',
           'Digitraffic-User': 'PortOfCall/0.1', 'Accept-Encoding': 'gzip'}
PORT_CODES = {'helsinki': 'FIHEL', 'turku': 'FITKU', 'rauma': 'FIRAU', 'rotterdam': 'NLRTM',
              'antwerp': 'BEANR', 'hamburg': 'DEHAM', 'bremerhaven': 'DEBRV', 'felixstowe': 'GBFXT',
              'southampton': 'GBSOU', 'los-angeles-long-beach': 'USLAX', 'new-york-new-jersey': 'USNYC',
              'savannah': 'USSAV', 'houston': 'USHOU', 'seattle': 'USSEA', 'charleston': 'USCHS',
              'singapore': 'SGSIN', 'shanghai-yangshan': 'CNSHA', 'busan-new-port': 'KRPUS'}
# These factual aliases are deliberately small and exact. Composite harbor areas
# do not imply that both component ports share a UN/LOCODE.
LOCAL_COUNTRIES = {code[:2]: HARBORS[key]['country'] for key, code in PORT_CODES.items()}
LOCAL_PORTS = {code: dict(code=code, name=HARBORS[key]['name'], country=HARBORS[key]['country'], position=HARBORS[key]['center'])
               for key, code in PORT_CODES.items() if key not in ('shanghai-yangshan', 'busan-new-port')}
LOCAL_PORTS.update(USLAX=dict(code='USLAX', name='Los Angeles', country=LOCAL_COUNTRIES['US'], position=[-118.25, 33.74]),
                   USLGB=dict(code='USLGB', name='Long Beach', country=LOCAL_COUNTRIES['US'], position=[-118.21, 33.75]))
# Reviewed exact CC0 reference: Q1792 explicitly has UN/LOCODE PLGDN.
# City-level name/country only; no guessed destination coordinates are supplied.
LOCAL_PORTS['PLGDN'] = dict(code='PLGDN', name='Gdańsk', country='Poland',
    source='Reviewed Wikidata port reference', url='https://www.wikidata.org/wiki/Q1792',
    license='https://creativecommons.org/publicdomain/zero/1.0/')
LOCAL_COUNTRIES['PL'] = 'Poland'
LOCAL_PORTS['LVMRX'] = dict(code='LVMRX', name='Mērsrags', country='Latvia',
    source='UNECE UN/LOCODE', url='https://service.unece.org/trade/locode/lv.htm')
LOCAL_COUNTRIES['LV'] = 'Latvia'
ALIASES = {k: v for code, v in LOCAL_PORTS.items() for k in (code, v['name'].upper())}
ALIASES.update({name.upper(): LOCAL_PORTS[code] for name, code in
                [('Helsinki', 'FIHEL'), ('Turku', 'FITKU'), ('Rauma', 'FIRAU'), ('Rotterdam', 'NLRTM'),
                 ('Antwerp', 'BEANR'), ('Hamburg', 'DEHAM'), ('Singapore', 'SGSIN'), ('Seattle', 'USSEA')]})


def port_key(raw):
    key = re.sub(r'\s+', '', raw.upper()) if isinstance(raw, str) else ''
    return key if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}', key) else None


def locode_id(key):
    # Wikidata stores UN/LOCODE (P1937) with a space: "GB IMM". AIS crews type
    # either form; port_key normalizes to "GBIMM" for display and local data.
    return key[:2]+' '+key[2:]


def cached(store, key, now):
    return store.reference(CACHE_VERSION+key, now)


def save_cache(store, key, payload, now, ttl):
    store.save_reference(CACHE_VERSION+key, payload, now, ttl)


def resolve_port(store, raw, now):
    if not raw: return None
    local = ALIASES.get(raw.strip().upper()) or LOCAL_PORTS.get(port_key(raw))
    if local: return {**local, 'source': local.get('source','Reviewed harbor catalog')}
    key = port_key(raw)
    hit = cached(store, 'port:'+locode_id(key), now) if key else None
    if hit and hit[1]:
        result = dict(hit[1])
        result['country'] = result.get('country') or country_name(store, key[:2], now)
        return result
    return None


def enrich_card(store, port, focus, now, *, calls=None):
    destination = focus.get('destination')
    focus['destination_port'] = resolve_port(store, destination['value'], now) if destination else None
    hit = cached(store, 'ship:'+focus['imo'], now) if focus.get('imo') else None
    if hit and hit[1]: focus['enrichment'] = {**hit[1], 'fetched_at': iso(hit[0])}
    mid = radio_mid(focus['mmsi'])
    allocation = cached(store, 'mid:'+mid, now) if mid else None
    if allocation and allocation[1] and allocation[1].get('code'):
        focus['flag'] = dict(value=country_name(store, allocation[1]['code'], now) or allocation[1]['name'], code=allocation[1].get('code'),
                             label='Flag (AIS)', inferred=True, method='mmsi_mid',
                             source='Wikidata / ITU MID assignment', url=allocation[1]['url'],
                             fetched_at=iso(allocation[0]))
    if focus.get('enrichment'):
        registry = focus['enrichment'].get('registry_country')
        if registry:
            focus['registry_country'] = registry
            if not focus.get('flag'):
                focus['flag'] = dict(value=registry['value'], label='Registry (Wikidata)',
                                     inferred=False, method='registry_reference', **{k:v for k,v in registry.items() if k!='value'})
        focus['built_in'] = focus['enrichment'].get('built_in')
    code = PORT_CODES.get(port['id'])
    observed = epoch(focus['reported_at'])
    for ts, call in store.recent_calls(now) if calls is None else calls:
        if call['port'] != code: continue
        if focus.get('imo') and call.get('imo') and focus['imo'] != call['imo']: continue
        if not ((focus.get('imo') and focus['imo'] == call.get('imo')) or focus['mmsi'] == call.get('mmsi')): continue
        if not call.get('ata') or not 0 <= observed-call['ata'] < 7*86400: continue
        if call.get('atd') and call['atd'] <= observed: continue
        # Use an actual current visit record; never turn a planned or old call into origin.
        nationality = call.get('nationality')
        focus['flag_reported_country_code'] = nationality
        nation_name = country_name(store, nationality, now)
        if nation_name:
            focus['flag'] = dict(value=nation_name, code=nationality, label='Reported flag',
                                 inferred=False, method='portnet_nationality', source='Fintraffic / Digitraffic Portnet',
                                 reported_at=iso(ts), url='https://www.digitraffic.fi/en/marine-traffic/')
        previous = call.get('previous')
        if previous:
            resolved = resolve_port(store, previous, now)
            focus['origin'] = dict(value=resolved['name'] if resolved else previous, code=previous,
                                   country=resolved.get('country') if resolved else country_name(store, previous[:2], now),
                                   source='Fintraffic / Digitraffic Portnet', reported_at=iso(ts),
                                   url='https://www.digitraffic.fi/en/marine-traffic/',
                                   license='https://creativecommons.org/licenses/by/4.0/')
        break


def country_name(store, code, now):
    if not isinstance(code, str) or not re.fullmatch(r'[A-Z]{2}', code): return None
    if code in LOCAL_COUNTRIES: return LOCAL_COUNTRIES[code]
    hit = cached(store, 'country:'+code, now)
    return hit[1]['name'] if hit and hit[1] else None


def current_values(entity, prop, now):
    """Current reference roles: reject ended, future and ambiguous dated claims."""
    values = []
    for claim in entity.get('claims', {}).get(prop, []):
        if claim.get('rank') == 'deprecated': continue
        qualifiers = claim.get('qualifiers', {})
        if 'P582' in qualifiers: continue
        if 'P580' in qualifiers:
            try:
                starts = [q['datavalue']['value'] for q in qualifiers['P580']]
                if not starts or any(v.get('precision', 0)<11 or epoch(v['time'].lstrip('+'))>now for v in starts): continue
            except (KeyError, TypeError, ValueError): continue
        snak = claim.get('mainsnak', {})
        if snak.get('snaktype') == 'value' and 'datavalue' in snak:
            values.append((claim.get('rank')=='preferred', snak['datavalue']['value']))
    preferred = [v for rank, v in values if rank]
    return preferred or [v for _, v in values]


def single_ref(entity, prop, now):
    vals = current_values(entity, prop, now)
    ids = list(dict.fromkeys(v['id'] for v in vals if isinstance(v, dict) and re.fullmatch(r'Q\d+', v.get('id', ''))))
    return ids[0] if len(ids)==1 else None


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
        mid = radio_mid(focus.get('mmsi'))
        if mid: keys.append(('mid', mid))
        if focus.get('imo'): keys.append(('ship', focus['imo']))
        for raw in [focus.get('destination', {}).get('value') if focus.get('destination') else None,
                    focus.get('origin', {}).get('code') if focus.get('origin') else None]:
            code = port_key(raw)
            if code and code not in LOCAL_PORTS: keys.append(('port', locode_id(code)))
        flag_code = focus.get('flag_reported_country_code') or (focus.get('flag', {}).get('code') if focus.get('flag') else None)
        if flag_code and flag_code not in LOCAL_COUNTRIES: keys.append(('country', flag_code))
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
        data = await self.request(session, action='query', list='search', srsearch=f'haswbstatement:"{prop}={identifier}"',
                                  srnamespace=0, srlimit=4)
        hits = data.get('query', {}).get('search', [])
        if not hits or len(hits) > 3: return None
        ids = [h['title'] for h in hits if re.fullmatch(r'Q\d+', h.get('title', ''))]
        if not ids: return None
        entities = (await self.request(session, action='wbgetentities', ids='|'.join(ids), props='claims|labels', languages='en')).get('entities', {})
        def norm(value): return value.replace(' ', '') if isinstance(value, str) else value
        exact = [e for e in entities.values() if norm(identifier) in [norm(v) for v in claim_values(e, prop)]]
        return exact[0] if len(exact) == 1 else None

    async def refresh(self, session, kind, key):
        token, now = kind+':'+key, self.clock()
        hit = cached(self.store, token, now)
        if hit: return hit[1]
        try:
            entity = await self.lookup(session, {'ship':'P458','port':'P1937','mid':'P2979','country':'P297'}[kind], key)
            result = None
            if entity:
                source = dict(source='Wikidata', url='https://www.wikidata.org/wiki/'+entity['id'], license='https://creativecommons.org/publicdomain/zero/1.0/')
                if kind in ('mid', 'country'):
                    codes = current_values(entity, 'P297', now)
                    code = codes[0] if len(codes)==1 and isinstance(codes[0], str) and re.fullmatch(r'[A-Z]{2}',codes[0]) else None
                    country_label = label(entity)
                    allocation_area = None
                    # Some MIDs identify a radio-registration area, e.g. Madeira,
                    # rather than a country/territory with its own ISO code.
                    if kind=='mid' and not code:
                        parent = single_ref(entity, 'P17', now)
                        if parent:
                            countries = (await self.request(session, action='wbgetentities', ids=parent, props='labels|claims', languages='en')).get('entities', {})
                            country = countries.get(parent, {})
                            codes = current_values(country, 'P297', now)
                            if len(codes)==1 and isinstance(codes[0],str) and re.fullmatch(r'[A-Z]{2}',codes[0]) and label(country):
                                allocation_area, country_label, code = label(entity), label(country), codes[0]
                    if country_label:
                        result = dict(name=LOCAL_COUNTRIES.get(code, country_label), code=code, allocation_area=allocation_area, **source)
                        if code: save_cache(self.store, 'country:'+code, result, now, 30*86400)
                elif kind == 'port':
                    coords = claim_values(entity, 'P625')
                    valid = [c for c in coords if c.get('globe') == 'http://www.wikidata.org/entity/Q2'
                             and isinstance(c.get('longitude'), (int, float)) and isinstance(c.get('latitude'), (int, float))
                             and -180 <= c['longitude'] <= 180 and -85 <= c['latitude'] <= 85]
                    if len(valid) == 1 and label(entity):
                        country = country_name(self.store, key[:2], now)
                        country_id = single_ref(entity, 'P17', now)
                        if country_id and not country:
                            countries = (await self.request(session, action='wbgetentities', ids=country_id, props='labels', languages='en')).get('entities', {})
                            country = label(countries.get(country_id, {}))
                        result = dict(code=key.replace(' ', ''), name=label(entity), country=country, position=[valid[0]['longitude'], valid[0]['latitude']], **source)
                else:
                    refs = {}
                    for prop, title in [('P289', 'Class'), ('P176', 'Builder'), ('P137', 'Operator'),
                                        ('P1071', 'Creation site'), ('P8047', 'Registry')]:
                        ref = single_ref(entity, prop, now)
                        if ref: refs[title] = ref
                    entities = {}
                    if refs:
                        entities = (await self.request(session, action='wbgetentities', ids='|'.join(sorted(set(refs.values()))), props='labels|claims', languages='en')).get('entities', {})
                    facts = [dict(label=title, value=label(entities.get(qid, {}))) for title, qid in refs.items()
                             if title in ('Class','Builder','Operator') and label(entities.get(qid, {}))]
                    dates = claim_values(entity, 'P729')
                    if len(dates) == 1 and isinstance(dates[0], dict) and dates[0].get('precision', 0) >= 9:
                        match = re.match(r'^\+(\d{4})-', dates[0].get('time', ''))
                        if match and 1700 <= int(match[1]) <= datetime.fromtimestamp(now, timezone.utc).year:
                            facts.append(dict(label='In service', value=match[1]))
                    registry = entities.get(refs.get('Registry'), {})
                    registry_country = dict(value=label(registry), source='Wikidata', url=source['url'], fetched_at=iso(now)) if label(registry) else None
                    site_id = refs.get('Creation site')
                    method = 'creation_site'
                    if not site_id:
                        builder_id = refs.get('Builder')
                        builder = entities.get(builder_id, {})
                        # A company headquarters is not a construction site. Only
                        # an explicitly identified shipyard is eligible as fallback.
                        types = claim_values(builder, 'P31')
                        if any(isinstance(v, dict) and v.get('id')=='Q190928' for v in types):
                            site_id, method = builder_id, 'builder_shipyard'
                    site = entities.get(site_id, {})
                    country_id = single_ref(site, 'P17', now) if site else None
                    built_in = None
                    if country_id:
                        countries = (await self.request(session, action='wbgetentities', ids=country_id, props='labels', languages='en')).get('entities', {})
                        if label(countries.get(country_id, {})):
                            built_in = dict(value=label(countries[country_id]), label='Built in' if method=='creation_site' else 'Shipyard country',
                                            method=method, site=label(site), source='Wikidata',
                                            url='https://www.wikidata.org/wiki/'+site_id, fetched_at=iso(now))
                    if facts or registry_country or built_in:
                        result = dict(facts=facts[:4], registry_country=registry_country, built_in=built_in, **source)
            save_cache(self.store, token, result, now, 30*86400 if result else 7*86400)
            return result
        except Exception as exc:
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
                                 nationality=call.get('nationality') if re.fullmatch(r'[A-Z]{2}', str(call.get('nationality',''))) else None,
                                 ata=min(arrivals) if arrivals else None, atd=max(departures) if departures else None)
                    self.store.save_call(str(call['portCallId']), ts, clean)
                except (ValueError, KeyError, TypeError): continue
            self.store.commit()
        except Exception as exc:
            log.warning('optional_portnet_unavailable error=%s', type(exc).__name__)

    async def run(self):
        import aiohttp
        async with aiohttp.ClientSession(trust_env=True, timeout=aiohttp.ClientTimeout(total=30, sock_connect=10)) as session:
            while True:
                await self.portnet(session)
                try: kind, key = await asyncio.wait_for(self.queue.get(), timeout=60)
                except asyncio.TimeoutError: continue
                try: await self.refresh(session, kind, key)
                finally:
                    self.pending.discard(kind+':'+key)
                    self.queue.task_done()
