"""One shared, persistent subject per harbor; no visitor or voyage tracking."""
import hashlib
import math
import re
from .facts import ship_type, NAVIGATION, text, infer_eta
from .model import contains, epoch, iso, viewport, harbor_view

HOLD = 3600
COOLDOWN = 24 * 3600
MAX_AGE = 15 * 60
PRIORITY_MARGIN = 15  # Comparable information + movement scores compete.


def value(vessel, key):
    return vessel.get('facts', {}).get(key, {}).get('value')


def eligible(vessel, now):
    return (0 <= now-epoch(vessel['reported_at']) < MAX_AGE and bool(text(vessel.get('name'))) and vessel.get('name') != vessel['mmsi']
            and len(vessel.get('facts', {})) + bool(vessel.get('type')) >= 2)


def ship_record(store, vessel, now):
    """(looked_up, record) for the ship's cached Wikidata entry, by IMO number."""
    from .enrichment import cached
    number = value(vessel, 'imo')
    hit = cached(store, 'ship:'+number, now) if number else cached(store, 'ship_mmsi:'+vessel['mmsi'], now)
    return (hit is not None, hit[1] if hit else None)


def knowledge(store, vessel, now, *, port=None, calls=None):
    """Available on-screen card content, 0-100; cached data only.

    Identifiers, pending lookups and facts omitted from the presentation earn
    nothing. Reuse the actual copy builder so inference and ETA rules agree.
    """
    from .enrichment import enrich_card
    from .display import focus_copy
    from .destinations import parse
    focus = card(vessel, now, '', now)
    enrich_card(store, port or {'id': None}, focus, now, calls=calls)
    shown = focus_copy(focus)
    score = 5*bool(shown['vessel_type'] and shown['vessel_type'] != 'Vessel') + 5*bool(shown['flag'])
    if shown['journey']:
        destination = value(vessel, 'destination')
        label = parse(destination)['text'] if destination else None
        # Opaque run-together strings are not as informative as named places.
        readable = bool(focus.get('destination_port') or focus.get('destination_term') or
                        (label and not re.fullmatch(r'[A-Z0-9_-]{4,}', label)))
        origin = focus.get('origin') or {}
        readable = readable or bool(origin.get('value') and origin['value'] != origin.get('code'))
        score += 15 if readable else 5
    score += 10*bool(shown['eta'])
    score += 10*len(shown['measurements'])  # length and width, at most two
    score += 15*len(shown['highlights'])  # at most two visible reference facts
    score += 15*bool(shown['details'])  # sourced build/shipyard country
    return min(score, 100)


def motion_score(vessel):
    # Low AIS speeds may be drift or manoeuvring, not sustained travel.
    speed = vessel.get('speed_knots')
    if speed is None or speed < 1: return 0
    return 30 if speed >= 3 else 15


def reason_for(vessel, store=None, now=None):
    if store is not None and ship_record(store, vessel, now)[1]: return 'Ship record available'
    if value(vessel, 'destination'): return 'Reported voyage details'
    if value(vessel, 'length_m'): return 'Reported vessel dimensions'
    return 'Vessel variety in this harbor'


def choose(store, port, vessels, now):
    candidates = [v for v in vessels if contains(port['bbox'], v['position']) and eligible(v, now)]
    if not candidates: return None
    calls = store.recent_calls(now)
    known = {v['mmsi']: knowledge(store, v, now, port=port, calls=calls) for v in candidates}
    # Joint priority lets motion compete with metadata before the shortlist.
    priority = {v['mmsi']: .6*known[v['mmsi']] + motion_score(v) for v in candidates}
    history = store.focus_history(port['id'])
    unseen = [v for v in candidates if now-history.get(v['mmsi'], (0, None))[0] >= COOLDOWN]
    pool = unseen or candidates  # Small harbors may repeat rather than fabricate a subject.
    current = store.current_focus(port['id'])
    if current and 0 <= now-current[1] < HOLD:
        held = next((v for v in candidates if v['mmsi'] == current[0]), None)
        if held:
            # A hold prevents small fluctuations, not a meaningful upgrade.
            # Recheck information and motion even when the held ship is moving.
            upgrades = [v for v in pool if priority[v['mmsi']] >= priority[held['mmsi']]+PRIORITY_MARGIN]
            if not upgrades: return held, current[1], reason_for(held, store, now)
            pool = upgrades  # An early replacement must actually improve on the held ship.
    best = max(priority[v['mmsi']] for v in pool)
    pool = [v for v in pool if priority[v['mmsi']] >= best-PRIORITY_MARGIN]
    lengths = sorted(value(v, 'length_m') for v in candidates if value(v, 'length_m'))
    recent_types = [cat for _, cat in sorted(history.values(), reverse=True)[:3] if cat]

    def score(v):
        length = value(v, 'length_m')
        size = 2 * sum(n <= length for n in lengths)/len(lengths) if length and lengths else 0
        novelty = min(4, max(0, (now-history.get(v['mmsi'], (0, None))[0])/COOLDOWN*4))
        # Unknown categories never receive a rarity bonus. Prefer finer AIS type codes.
        cat = str(value(v, 'ship_type_code') or v.get('type') or '')
        variety = 4/(1+recent_types.count(cat)) if cat else 0
        return priority[v['mmsi']]+size+novelty+variety

    shortlist = sorted(pool, key=lambda v: (-score(v), v['mmsi']))[:5]
    def weighted_key(v):
        seed = f"{port['id']}:{int(now//HOLD)}:{v['mmsi']}".encode()
        u = (int.from_bytes(hashlib.sha256(seed).digest()[:8], 'big')+1)/(2**64+1)
        # Squared weights favor the best-known ships while keeping some variety.
        return -math.log(u)/max(score(v), 1)**2
    selected = min(shortlist, key=weighted_key)
    reason = reason_for(selected, store, now)
    mid = selected['mmsi']
    cat = str(value(selected, 'ship_type_code') or selected.get('type') or '')
    store.save_focus(port['id'], mid, now, reason, cat)
    return selected, now, reason


def lookups_worth_making(store, port, vessels, now, limit=3):
    """IMO numbers of likely Spotlight subjects whose ship record is not yet cached.

    Lookups do not add speculative selection points. Prefer moving subjects
    with useful existing card content; length only breaks otherwise equal ties.
    """
    candidates = [v for v in harbor_candidates(port,vessels,now) if contains(port['bbox'], v['position'])
                  and value(v, 'imo') and not ship_record(store, v, now)[0]]
    calls = store.recent_calls(now)
    candidates.sort(key=lambda v: (-motion_score(v), -knowledge(store, v, now, port=port, calls=calls),
                                   -(value(v, 'length_m') or 0), v['mmsi']))
    return [value(v, 'imo') for v in candidates[:limit]]


def harbor_candidates(port,vessels,now):
    """Prefer a shared subject visible in both fixed device views.

    If their safe areas have no eligible subject in common, either may supply
    one; the client retains its existing per-layout overview fallback.
    """
    devices = ('og','x') if port.get('cameras') else ('og',)
    visible = [spotlight_areas(port,harbor_view(port,device)) for device in devices]
    candidates = [v for v in vessels if eligible(v,now)]
    common = [v for v in candidates if all(area(v) for area in visible)]
    return common or [v for v in candidates if any(area(v) for area in visible)]


def spotlight_areas(port, box):
    """Where a Spotlight subject stays visible in a fixed harbor view.

    The view never moves for Spotlight, so the subject must be on screen in
    the reference viewport: away from edges and the bottom-left harbor card.
    Compact layouts still check actual screen visibility and may use overview.
    All safely visible ships compete together, without a centrality preference.
    """
    w, s, e, n = box
    dx, dy = e-w, n-s
    safe = (w+dx*.06, s+dy*.08, e-dx*.06, n-dy*.08)
    card = (w, s, w+dx*.5, s+dy*.34)
    def visible(v):
        p = v['position']
        return contains(safe, p) and not contains(card, p)
    return visible


def focus_viewport(port, vessel, scale):
    box = viewport(port, scale)
    x, y = vessel['position']
    dx, dy = (box[2]-box[0])/2, (box[3]-box[1])/2
    return [max(-180, x-dx), max(-85, y-dy), min(180, x+dx), min(85, y+dy)]


def card(v, selected_at, reason, now):
    facts = v.get('facts', {})
    rows = []
    def add(label, val, key=None):
        if val is not None:
            meta = facts.get(key, {}) if key else {}
            rows.append(dict(label=label, value=str(val), reported_at=meta.get('reported_at', v['reported_at']),
                             source=meta.get('source', 'AIS position report')))
    add('Type', ship_type(value(v, 'ship_type_code'), v.get('type')), 'ship_type_code')
    length, beam = value(v, 'length_m'), value(v, 'beam_m')
    if length: add('Length / beam' if beam else 'Length', f'{length} × {beam} m' if beam else f'{length} m', 'length_m')
    if v.get('speed_knots') is not None: add('Speed', f"{v['speed_knots']:g} kn")
    if v.get('navigation_status') in NAVIGATION: add('Reported status', NAVIGATION[v['navigation_status']])
    add('Call sign', value(v, 'call_sign'), 'call_sign')
    add('IMO', value(v, 'imo'), 'imo')
    add('MMSI', v['mmsi'])
    # A separate identifier list prevents six-row limits from hiding enrichment keys.
    return dict(mmsi=v['mmsi'], imo=value(v, 'imo'), name=v['name'], position=v['position'],
                reported_at=v['reported_at'], selected_at=iso(selected_at), selected_until=iso(selected_at+HOLD),
                reason=reason, facts=rows[:6], dimensions=dict(length_m=length,beam_m=beam), destination=facts.get('destination'), eta=facts.get('eta'),
                origin=None, destination_port=None, enrichment=None,
                eta_estimate=infer_eta(facts.get('eta'), now), flag=None, built_in=None)
