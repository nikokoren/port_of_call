"""One shared, persistent subject per harbor; no visitor or voyage tracking."""
import hashlib
import math
from .facts import ship_type, NAVIGATION, text, infer_eta
from .model import contains, epoch, iso, viewport

HOLD = 3 * 3600
COOLDOWN = 24 * 3600
MAX_AGE = 15 * 60
KNOWLEDGE_MARGIN = 15  # Ships within this many points of the best-known compete.


def value(vessel, key):
    return vessel.get('facts', {}).get(key, {}).get('value')


def eligible(vessel, now):
    return (0 <= now-epoch(vessel['reported_at']) < MAX_AGE and bool(text(vessel.get('name'))) and vessel.get('name') != vessel['mmsi']
            and len(vessel.get('facts', {})) + bool(vessel.get('type')) >= 2)


# AIS details a Spotlight card shows when present.
CARD_FACTS = ('destination', 'eta', 'length_m', 'beam_m', 'imo', 'call_sign', 'ship_type_code')


def ship_record(store, vessel, now):
    """(looked_up, record) for the ship's cached Wikidata entry, by IMO number."""
    from .enrichment import cached
    number = value(vessel, 'imo')
    hit = cached(store, 'ship:'+number, now) if number else None
    return (hit is not None, hit[1] if hit else None)


def knowledge(store, vessel, now):
    """How much a Spotlight card can say about this ship, 0-100.

    AIS details count first; a reference record (builder, operator, year in
    service, where it was built) counts most; a destination that resolves to a
    named port adds a little. An IMO number not yet looked up is a promise of a
    record, so it scores a little too.
    """
    from .enrichment import resolve_port
    score = 6*sum(value(vessel, key) is not None for key in CARD_FACTS)
    looked_up, record = ship_record(store, vessel, now)
    if record:
        score += 10*len(record.get('facts') or []) + 8*bool(record.get('built_in')) + 6*bool(record.get('registry_country'))
    elif value(vessel, 'imo') and not looked_up:
        score += 8
    destination = value(vessel, 'destination')
    if destination and resolve_port(store, destination, now): score += 6
    return min(score, 100)


def reason_for(vessel, store=None, now=None):
    if store is not None and ship_record(store, vessel, now)[1]: return 'Ship record available'
    if value(vessel, 'destination'): return 'Reported voyage details'
    if value(vessel, 'length_m'): return 'Reported vessel dimensions'
    return 'Vessel variety in this harbor'


def choose(store, port, vessels, now):
    candidates = [v for v in vessels if contains(port['bbox'], v['position']) and eligible(v, now)]
    current = store.current_focus(port['id'])
    if current and 0 <= now-current[1] < HOLD:
        held = next((v for v in candidates if v['mmsi'] == current[0]), None)
        if held: return held, current[1], reason_for(held, store, now)
    if not candidates: return None
    history = store.focus_history(port['id'])
    unseen = [v for v in candidates if now-history.get(v['mmsi'], (0, None))[0] >= COOLDOWN]
    pool = unseen or candidates  # Small harbors may repeat rather than fabricate a subject.
    # Prefer the ships a card can say most about; vary among comparably known ones.
    known = {v['mmsi']: knowledge(store, v, now) for v in pool}
    best = max(known.values())
    pool = [v for v in pool if known[v['mmsi']] >= best-KNOWLEDGE_MARGIN]
    lengths = sorted(value(v, 'length_m') for v in candidates if value(v, 'length_m'))
    recent_types = [cat for _, cat in sorted(history.values(), reverse=True)[:3] if cat]

    def score(v):
        # What the card can say about the ship matters most.
        quality = .6*known.get(v['mmsi'], 0)
        length = value(v, 'length_m')
        size = 25 * sum(n <= length for n in lengths)/len(lengths) if length and lengths else 0
        novelty = min(20, max(0, (now-history.get(v['mmsi'], (0, None))[0])/COOLDOWN*20))
        # Unknown categories never receive a rarity bonus. Prefer finer AIS type codes.
        cat = str(value(v, 'ship_type_code') or v.get('type') or '')
        variety = 15/(1+recent_types.count(cat)) if cat else 0
        movement = 10 if (v.get('speed_knots') or 0) >= 0.5 else 0
        return quality+size+novelty+variety+movement

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


def lookups_worth_making(store, port, vessels, now, limit=1):
    """IMO numbers of likely Spotlight subjects whose ship record is not yet cached.

    Looking these up ahead of time lets the next selection see which ships
    have a reference record. Largest first, since big ships are the likeliest
    to have one.
    """
    candidates = [v for v in vessels if contains(port['bbox'], v['position']) and eligible(v, now)
                  and value(v, 'imo') and not ship_record(store, v, now)[0]]
    candidates.sort(key=lambda v: (-(value(v, 'length_m') or 0), v['mmsi']))
    return [value(v, 'imo') for v in candidates[:limit]]


def spotlight_areas(port, box):
    """Where a Spotlight subject stays visible in a fixed harbor view.

    The view never moves for Spotlight, so the subject must be on screen in
    every layout: away from the edges and from the bottom-left harbor card.
    Smaller layouts show the middle of the view, so central ships come first.
    """
    w, s, e, n = box
    dx, dy = e-w, n-s
    fx, fy = port.get('focus') or port['center']
    safe = (w+dx*.06, s+dy*.08, e-dx*.06, n-dy*.08)
    card = (w, s, w+dx*.5, s+dy*.34)
    central = (fx-dx*.25, fy-dy*.17, fx+dx*.25, fy+dy*.17)
    def visible(v):
        p = v['position']
        return contains(safe, p) and not contains(card, p)
    return visible, lambda v: visible(v) and contains(central, v['position'])


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
