from datetime import datetime
from zoneinfo import ZoneInfo
from .model import DEFAULT_SCALE, harbor_zoom, viewport, contains, select, epoch, iso, bearing, map_candidates_view
from .spotlight import choose, focus_viewport, card, spotlight_areas
from .display import focus_copy, label_voyage
from .port_facts import port_fact

MESSAGES = {
    'warming': 'Collecting vessel positions', 'empty': 'No recent vessel reports for this area',
    'stale': 'Latest positions may be outdated', 'unavailable': 'Vessel feed unavailable', 'ok': ''}


def snapshot(store, port, now, fresh=1800, ttl=3600, scale=DEFAULT_SCALE, demo=False, spotlight=False, fact_period=3600, map_mode=False):
    box = viewport(port, scale)
    harbor_vessels = store.vessels(now, ttl, port['bbox'])
    fetched = float(store.state('last_success') or 0)
    subject = None
    if spotlight and fetched and now-fetched < fresh:
        if scale == 'harbor':
            # Spotlight annotates the harbor view; it never moves the map. Pick
            # a safely visible subject; centrality does not affect its chances.
            visible = spotlight_areas(port, box)
            subject = choose(store, port, [v for v in harbor_vessels if visible(v)], now)
        else:
            subject = choose(store, port, harbor_vessels, now)
    focus = None
    if subject:
        vessel, selected_at, reason = subject
        if scale != 'harbor': box = focus_viewport(port, vessel, scale)
        focus = card(vessel, selected_at, reason, now)
        from .enrichment import enrich_card
        enrich_card(store, port, focus, now)
        focus['presentation'] = focus_copy(focus)
        focus['trail'] = store.movement(vessel, now)
    core = box
    if map_mode and scale=='harbor': box = map_candidates_view(port,core)
    all_vessels = [v for v in harbor_vessels if contains(box, v['position'])]
    latest = max((epoch(v['reported_at']) for v in all_vessels), default=None)
    if not fetched: status = 'warming'
    elif now-fetched >= ttl: status = 'unavailable'
    elif now-fetched >= fresh or (latest is not None and now-latest >= fresh): status = 'stale'
    elif not all_vessels: status = 'empty'
    else: status = 'ok'
    if status == 'unavailable': all_vessels = []
    from .labels import interest, rank
    scores = {v['mmsi']: interest(v, now, fresh) for v in all_vessels}
    available = [v for v in all_vessels if not focus or v['mmsi'] != focus['mmsi']]
    if map_mode:
        from .compact import MAP_LIMIT, CORE_LIMIT
        limit = MAP_LIMIT-bool(focus)
        vessels = select(available,core,min(CORE_LIMIT-bool(focus),limit),key=lambda v:scores[v['mmsi']])
        vessels += select([v for v in available if not contains(core,v['position'])],box,limit-len(vessels),key=lambda v:scores[v['mmsi']])
        chosen = {v['mmsi'] for v in vessels}
        if len(vessels)<limit:
            vessels += select([v for v in available if v['mmsi'] not in chosen],core,limit-len(vessels),key=lambda v:scores[v['mmsi']])
    else:
        vessels = select(available, box, 39 if focus else 40,key=lambda v:scores[v['mmsi']])
    if focus: vessels.insert(0, subject[0])
    # Labels use cached metadata only. Read relevant calls once for the batch;
    # this never opens per-ship network requests or infers an origin from motion.
    from .enrichment import enrich_card
    calls = store.recent_calls(now)
    from .enrichment import port_key
    markers, unresolved, reviews = [], {}, []
    for v in vessels:
        context = focus if focus and focus['mmsi'] == v['mmsi'] else card(v, now, '', now)
        if context is not focus: enrich_card(store, port, context, now, calls=calls)
        reviews.append(context)
        if context.get('destination') and not context.get('destination_port') and not context.get('destination_term'):
            code = port_key(context['destination'].get('value'))
            if code: unresolved[code] = unresolved.get(code,0)+1
        voyage = label_voyage(context)
        # Length sizes the map icon; the rest of the facts stay in the store.
        length = context.get('dimensions', {}).get('length_m') if context.get('dimensions') else None
        # Keep the rich facts/provenance in the store, not every overview marker.
        v = {k: val for k, val in v.items() if k != 'facts'}
        if voyage: v['voyage'] = voyage
        if isinstance(length, (int, float)) and not isinstance(length, bool) and length > 0: v['length_m'] = round(length)
        v['bearing_deg'] = bearing(v)
        v['stale'] = now-epoch(v['reported_at']) >= fresh
        # 5 decimal places is ~1m; keep payload small without moving markers materially.
        v['position'] = [round(c, 5) for c in v['position']]
        markers.append(v)
    # The Spotlight ship has its own card; the rest get a label order.
    rank([m for m in markers if not focus or m['mmsi'] != focus['mmsi']], scores, port)
    vessels = markers
    from .destination_review import record_many
    record_many(store, port['id'], reviews, now)
    from .landmarks import LANDMARKS
    zone = ZoneInfo(port['timezone'])
    def local(ts): return datetime.fromtimestamp(ts, zone).strftime('%H:%M %Z') if ts else None
    if focus:
        focus['reported_local'] = local(epoch(focus['reported_at']))
        voyage = focus.get('destination') or focus.get('eta')
        focus['voyage_age_minutes'] = int((now-epoch(voyage['reported_at']))//60) if voyage else None
    source = 'AISStream' if port['provider'] == 'aisstream' else 'Fintraffic / Digitraffic'
    if demo: source = 'Synthetic fixture — DEMO'
    # Fixed-zoom framing tells the map its zoom and centre; other scales fit the box.
    camera = dict(zoom=harbor_zoom(port), center=list(port.get('focus') or port['center'])) if scale == 'harbor' else None
    return dict(schema_version=1, display_mode='map', port=port, port_fact=port_fact(port['id'], now, fact_period), landmarks=LANDMARKS.get(port['id'],[]), viewport=box, camera=camera, source=source,
                attribution={'label': 'Fintraffic / digitraffic.fi · CC BY 4.0 · filtered AIS',
                    'url': 'https://www.digitraffic.fi/en/marine-traffic/',
                    'license': 'https://creativecommons.org/licenses/by/4.0/'} if port['provider']=='digitraffic' else None,
                snapshot_at=iso(now), fetched_at=iso(fetched) if fetched else None,
                latest_report_at=iso(latest) if latest else None,
                fetched_local=local(fetched), latest_report_local=local(latest),
                latest_report_age_minutes=int((now-latest)//60) if latest else None,
                status=status, message=MESSAGES[status], demo=demo,
                focus_requested=bool(spotlight), focus_mode='ship' if focus else 'harbor', focus=focus,
                focus_message='No suitable fresh ship · showing harbor' if spotlight and not focus else '',
                total=len(all_vessels), shown=len(vessels), omitted=len(all_vessels)-len(vessels), vessels=vessels,
                # Internal: destination codes to look up. Callers pop it before encoding.
                unresolved_ports=sorted(unresolved,key=lambda k:(-unresolved[k],k)))
