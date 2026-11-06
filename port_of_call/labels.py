"""Which ships are worth naming on the map.

The map can draw far more ships than it can name, so labels go to the ships
that tell the harbor's story of arrivals and departures: working ships on the
move, big ships, ships heading here or bound somewhere else, and a mix of
kinds and destinations rather than a row of moored yachts that all read "To
Hamburg". Ships whose last report is old come last.
"""
from .model import epoch
from .spotlight import value

# Big commercial traffic first; "other" covers tugs, pilots, yachts and service craft.
TYPE_WEIGHT = {'cargo': 3.0, 'tanker': 3.0, 'passenger': 2.5, 'fishing': 1.0, 'other': 0.5}
# Each label already given to the same kind of ship lowers the next one's priority.
REPEAT_PENALTY = 1.5


def _named(vessel):
    name = vessel.get('name')
    return bool(name) and name != vessel.get('mmsi')


def interest(vessel, now, fresh=1800):
    """A ship's own interest score, from what the store knows about it."""
    score = TYPE_WEIGHT.get(vessel.get('type'), 0.0)
    speed = vessel.get('speed_knots') or 0
    if speed >= 1: score += 3 + min(speed, 20)/10  # arriving, departing or passing through
    length = value(vessel, 'length_m')
    if isinstance(length, (int, float)) and not isinstance(length, bool) and length > 0:
        score += min(length, 300)/100
    if vessel.get('facts', {}).get('destination') or vessel.get('voyage'): score += 1.5
    # An old report may no longer be where the ship is: after every fresh ship.
    if now-epoch(vessel['reported_at']) >= fresh: score -= 20
    return score


def _city(port):
    return [part.strip() for part in port['name'].split(' — ')[0].split('/') if part.strip()]


def rank(markers, scores, port):
    """Set label_rank 1..n on named markers, best first.

    scores maps mmsi to interest(). Picks one at a time, lowering ships of a
    kind or destination that already has a label, so the names on screen vary.
    """
    cities = _city(port)
    def base(v):
        voyage = v.get('voyage') or ''
        here, moving = any(voyage.startswith('To ' + c) for c in cities), (v.get('speed_knots') or 0) >= 1
        # Arriving (heading here and moving) or bound elsewhere is news;
        # already lying at its destination is not.
        bonus = 1.0 if voyage and (moving or not here) else -1.0 if here else 0.0
        return scores.get(v['mmsi'], 0.0) + bonus
    pool = sorted((v for v in markers if _named(v)), key=lambda v: (-base(v), v['mmsi']))
    kinds, voyages, n = {}, {}, 0
    def score(v):
        repeats = kinds.get(v.get('type'), 0) + (voyages.get(v['voyage'], 0) if v.get('voyage') else 0)
        return base(v) - REPEAT_PENALTY*repeats
    while pool:
        best = max(pool, key=lambda v: (score(v), -pool.index(v)))
        pool.remove(best)
        n += 1
        best['label_rank'] = n
        kinds[best.get('type')] = kinds.get(best.get('type'), 0) + 1
        if best.get('voyage'): voyages[best['voyage']] = voyages.get(best['voyage'], 0) + 1
    return markers
