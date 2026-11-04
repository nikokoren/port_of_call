from datetime import datetime
from zoneinfo import ZoneInfo
from .model import viewport, contains, select, epoch, iso, bearing

MESSAGES = {
    'warming': 'Collecting vessel positions', 'empty': 'No recent vessel reports for this area',
    'stale': 'Latest positions may be outdated', 'unavailable': 'Vessel feed unavailable', 'ok': ''}


def snapshot(store, port, now, fresh=1800, ttl=3600, scale='standard', demo=False):
    box = viewport(port, scale)
    all_vessels = [v for v in store.vessels(now, ttl) if contains(box, v['position'])]
    latest = max((epoch(v['reported_at']) for v in all_vessels), default=None)
    fetched = float(store.state('last_success') or 0)
    if not fetched: status = 'warming'
    elif now-fetched >= ttl: status = 'unavailable'
    elif now-fetched >= fresh or (latest is not None and now-latest >= fresh): status = 'stale'
    elif not all_vessels: status = 'empty'
    else: status = 'ok'
    if status == 'unavailable': all_vessels = []
    vessels = select(all_vessels, box)
    for v in vessels:
        v['bearing_deg'] = bearing(v)
        v['stale'] = now-epoch(v['reported_at']) >= fresh
        # 5 decimal places is ~1m; keep payload small without moving markers materially.
        v['position'] = [round(c, 5) for c in v['position']]
    zone = ZoneInfo(port['timezone'])
    def local(ts): return datetime.fromtimestamp(ts, zone).strftime('%H:%M %Z') if ts else None
    source = 'AISStream' if port['provider'] == 'aisstream' else 'Fintraffic / Digitraffic'
    if demo: source = 'Synthetic fixture — DEMO'
    return dict(schema_version=1, display_mode='map', port=port, viewport=box, source=source,
                attribution={'label': 'Fintraffic / digitraffic.fi · CC BY 4.0 · filtered AIS',
                    'url': 'https://www.digitraffic.fi/en/marine-traffic/',
                    'license': 'https://creativecommons.org/licenses/by/4.0/'} if port['provider']=='digitraffic' else None,
                snapshot_at=iso(now), fetched_at=iso(fetched) if fetched else None,
                latest_report_at=iso(latest) if latest else None,
                fetched_local=local(fetched), latest_report_local=local(latest),
                latest_report_age_minutes=int((now-latest)//60) if latest else None,
                status=status, message=MESSAGES[status], demo=demo,
                total=len(all_vessels), shown=len(vessels), omitted=len(all_vessels)-len(vessels), vessels=vessels)
