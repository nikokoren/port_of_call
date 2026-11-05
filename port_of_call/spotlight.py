"""One shared, persistent subject per harbor; no visitor or voyage tracking."""
import hashlib
import math
from .facts import ship_type, NAVIGATION, text
from .model import contains, epoch, iso, viewport

HOLD = 3 * 3600
COOLDOWN = 24 * 3600
MAX_AGE = 15 * 60


def value(vessel, key):
    return vessel.get('facts', {}).get(key, {}).get('value')


def eligible(vessel, now):
    return (0 <= now-epoch(vessel['reported_at']) < MAX_AGE and bool(text(vessel.get('name'))) and vessel.get('name') != vessel['mmsi']
            and len(vessel.get('facts', {})) + bool(vessel.get('type')) >= 2)


def reason_for(vessel):
    if value(vessel, 'destination'): return 'Reported voyage details'
    if value(vessel, 'length_m'): return 'Reported vessel dimensions'
    return 'Vessel variety in this harbor'


def choose(store, port, vessels, now):
    candidates = [v for v in vessels if contains(port['bbox'], v['position']) and eligible(v, now)]
    current = store.db.execute('SELECT mmsi,selected_at,reason FROM focus_current WHERE port=?', (port['id'],)).fetchone()
    if current and 0 <= now-current[1] < HOLD:
        held = next((v for v in candidates if v['mmsi'] == current[0]), None)
        if held: return held, current[1], reason_for(held)
    if not candidates: return None
    history = {mid: (ts, category) for mid, ts, category in store.db.execute(
        'SELECT mmsi,ts,category FROM focus_history WHERE port=?', (port['id'],))}
    unseen = [v for v in candidates if now-history.get(v['mmsi'], (0, None))[0] >= COOLDOWN]
    pool = unseen or candidates  # Small harbors may repeat rather than fabricate a subject.
    lengths = sorted(value(v, 'length_m') for v in candidates if value(v, 'length_m'))
    recent_types = [cat for _, cat in sorted(history.values(), reverse=True)[:3] if cat]

    def score(v):
        facts = v.get('facts', {})
        quality = min(30, len(facts) * 5)
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
        return -math.log(u)/max(score(v), 1)
    selected = min(shortlist, key=weighted_key)
    reason = reason_for(selected)
    mid = selected['mmsi']
    cat = str(value(selected, 'ship_type_code') or selected.get('type') or '')
    store.db.execute('INSERT OR REPLACE INTO focus_current VALUES (?,?,?,?)', (port['id'], mid, now, reason))
    store.db.execute('INSERT OR REPLACE INTO focus_history VALUES (?,?,?,?)', (port['id'], mid, now, cat))
    store.db.execute('DELETE FROM focus_history WHERE port=? AND mmsi NOT IN (SELECT mmsi FROM focus_history WHERE port=? ORDER BY ts DESC LIMIT 64)', (port['id'], port['id']))
    store.commit()
    return selected, now, reason


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
    if value(v, 'draught_m'): add('Reported draught', f"{value(v, 'draught_m'):g} m", 'draught_m')
    add('Call sign', value(v, 'call_sign'), 'call_sign')
    add('IMO', value(v, 'imo'), 'imo')
    add('MMSI', v['mmsi'])
    # A separate identifier list prevents six-row limits from hiding enrichment keys.
    return dict(mmsi=v['mmsi'], imo=value(v, 'imo'), name=v['name'], position=v['position'],
                reported_at=v['reported_at'], selected_at=iso(selected_at), selected_until=iso(selected_at+HOLD),
                reason=reason, facts=rows[:6], destination=facts.get('destination'), eta=facts.get('eta'),
                origin=None, destination_port=None, enrichment=None)
