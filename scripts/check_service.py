"""Read-only live contract/freshness probe. Output contains aggregate counts only."""
import argparse
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def get(url, *, timeout=30):
    try: r = urlopen(Request(url, headers={'User-Agent': 'PortOfCall release monitor'}), timeout=timeout)
    except HTTPError as error: r = error
    with r:
        body = r.read(100_001)
        if len(body) > 100_000: raise ValueError('Oversized API body')
        return r.status, json.loads(body), len(body), r.headers


def check(origin, *, allow_degraded=False, all_framings=False):
    started = time.time()
    status, health, _, _ = get(origin+'/health')
    errors = []
    if status not in (200, 503) or health.get('status') not in ('ready', 'degraded'): errors.append('Invalid health contract')
    if not allow_degraded and status != 200: errors.append('Feed is not ready')
    status, catalog, _, _ = get(origin+'/api/v1/harbors')
    if status != 200 or not catalog.get('harbors'): raise ValueError('Harbor catalog unavailable')
    rows = []
    for port in catalog['harbors']:
        for scale in (('harbor', 'closer', 'standard', 'wider') if all_framings else ('harbor',)):
            for focus in (False, True):
                url = origin+'/api/v1/harbors/'+port['id']+'/vessels?scale='+scale+'&spotlight='+str(focus).lower()
                status, data, size, headers = get(url)
                if status != 200: raise ValueError('Snapshot HTTP failure for '+port['id'])
                if data.get('schema_version') != 1 or data.get('demo') is not False: raise ValueError('Wrong schema or demo payload')
                if size >= 15_000: raise ValueError('TRMNL payload budget exceeded')
                if data['port']['id'] != port['id'] or data['port']['provider'] != health['provider']: raise ValueError('Provider/catalog mismatch')
                if data['status'] not in ('ok', 'warming', 'empty', 'stale', 'unavailable'): raise ValueError('Unknown data state')
                if not allow_degraded and data['status'] in ('warming', 'stale', 'unavailable'): errors.append(port['id']+': '+data['status'])
                if data['shown'] != len(data['vessels']) or data['total'] < data['shown']: raise ValueError('Invalid vessel counts')
                mids = set()
                for vessel in data['vessels']:
                    if not re.fullmatch(r'\d{9}', vessel['mmsi']) or vessel['mmsi'] in mids: raise ValueError('Invalid/duplicate MMSI')
                    mids.add(vessel['mmsi'])
                    if 'voyage' in vessel and not isinstance(vessel['voyage'],str): raise ValueError('Invalid voyage label')
                    lon, lat = vessel['position']
                    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (lon, lat)): raise ValueError('Invalid coordinates')
                    if not -180 <= lon <= 180 or not -90 <= lat <= 90: raise ValueError('Invalid coordinate range')
                    reported = datetime.fromisoformat(vessel['reported_at'].replace('Z', '+00:00')).timestamp()
                    if not -5 <= time.time()-reported < 3660: raise ValueError('Expired or future vessel position')
                if data['status'] == 'unavailable' and data['vessels']: raise ValueError('Unavailable feed displays positions')
                subject = data.get('focus')
                if subject and (not focus or not data['vessels'] or data['vessels'][0]['mmsi'] != subject['mmsi']): raise ValueError('Featured marker missing')
                if subject and any('draught' in fact['label'].lower() for fact in subject.get('facts', [])): raise ValueError('Removed fact in card')
                rows.append(dict(port=port['id'], scale=scale, spotlight=focus, state=data['status'],
                                 total=data['total'], shown=data['shown'], focused=bool(subject),
                                 voyage_labels=sum(bool(v.get('voyage')) for v in data['vessels']), bytes=size))
    # Recipe endpoint: one selected harbor is pinned; none rotates through the catalog.
    ids = [h['id'] for h in catalog['harbors']]
    status, data, _, _ = get(origin+'/api/v1/vessels?harbors='+ids[-1]+'&spotlight=false')
    if status != 200 or data['port']['id'] != ids[-1]: errors.append('Selected harbor not pinned')
    status, data, _, _ = get(origin+'/api/v1/vessels?harbors=&spotlight=false')
    if status != 200 or data['port']['id'] not in ids: errors.append('Empty selection did not rotate within the catalog')
    for path, code in [('/api/v1/harbors/not-a-port/vessels', 404),
                       ('/api/v1/vessels?harbors='+ids[0]+'&spotlight=maybe', 400),
                       ('/demo/api/v1/harbors/'+catalog['harbors'][0]['id']+'/vessels', 404),
                       ('/api/v1/harbors/'+catalog['harbors'][0]['id']+'/vessels?scale=bad', 400)]:
        if get(origin+path)[0] != code: errors.append('Invalid route accepted')
    return dict(checked_at=datetime.now(timezone.utc).isoformat(), origin=origin, provider=health['provider'],
                health=health['status'], seconds=round(time.time()-started, 2), snapshots=rows,
                passed=not errors, errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origin')
    parser.add_argument('--allow-local', action='store_true')
    parser.add_argument('--allow-degraded', action='store_true')
    parser.add_argument('--all-framings', action='store_true')
    parser.add_argument('--output', default='var/release-check.json')
    args = parser.parse_args()
    url = urlsplit(args.origin)
    if url.username or url.password or url.query or url.fragment or not url.hostname:
        parser.error('Use an origin without credentials/query/fragment')
    if url.scheme != 'https' and not (args.allow_local and url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost')):
        parser.error('Public probes require HTTPS')
    try: report = check(args.origin.rstrip('/'), allow_degraded=args.allow_degraded, all_framings=args.all_framings)
    except Exception as exc:
        report = dict(checked_at=datetime.now(timezone.utc).isoformat(), origin=args.origin,
                      provider='unknown', health='unreachable', passed=False, snapshots=[],
                      errors=[str(exc) if isinstance(exc, ValueError) else type(exc).__name__])
    path = Path(args.output);path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(report['provider'], report['health'], len(report['snapshots']), 'snapshots;', 'passed' if report['passed'] else 'FAILED')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__': main()
