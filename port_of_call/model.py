"""Provider-independent validation. Coordinates are always longitude, latitude."""
import json
import math
import re
from datetime import datetime, timezone
from importlib.resources import files

HARBORS = {h['id']: h for h in json.loads(files('port_of_call').joinpath('harbors.json').read_text())}


def epoch(value):
    if isinstance(value, bool):
        raise ValueError('Invalid timestamp')
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        # AISStream sometimes appends nanoseconds and ' +0000 UTC'.
        value = re.sub(r'\s+\+0000 UTC$', '+00:00', value).replace('Z', '+00:00')
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            raise ValueError('Timezone required')
        result = dt.timestamp()
    else:
        raise ValueError('Missing timestamp')
    if not math.isfinite(result):
        raise ValueError('Invalid timestamp')
    return result


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    return float(value) if math.isfinite(value) and low <= value < high else None


def mmsi(value):
    value = str(value)
    # Include leading zero MMSIs, but never all zero or an AIS unavailable value.
    return value if re.fullmatch(r'\d{9}', value) and int(value) > 0 else None


def name(value):
    # Preserve plain text only. The renderer also uses textContent / escape.
    return re.sub(r'[<>\x00-\x1f\x7f]', '', str(value or '')).strip(' @')[:48] or None


def category(value):
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if 70 <= value <= 79: return 'cargo'
    if 80 <= value <= 89: return 'tanker'
    if 60 <= value <= 69: return 'passenger'
    if value == 30: return 'fishing'
    return 'other' if 20 <= value <= 99 else None


def contains(bbox, position):
    west, south, east, north = bbox
    lon, lat = position
    return south <= lat <= north and (west <= lon <= east if west <= east else lon >= west or lon <= east)


def position(mid, lon, lat, reported_at, now, ttl=3600, **fields):
    mid = mmsi(mid)
    lon, lat = number(lon, -180, 180.000001), number(lat, -90, 90.000001)
    ts = epoch(reported_at)
    # No future positions; no re-dating reports to the HTTP fetch time.
    if not mid or lon is None or lat is None or not 0 <= now - ts < ttl:
        raise ValueError('Invalid, expired or future position')
    return dict(mmsi=mid, position=[lon, lat], reported_at=iso(ts),
                heading_deg=number(fields.get('heading'), 0, 360),
                course_deg=number(fields.get('course'), 0, 360),
                speed_knots=number(fields.get('speed'), 0, 102.3))


def bearing(vessel):
    if vessel['heading_deg'] is not None:
        return vessel['heading_deg']
    if (vessel['speed_knots'] or 0) >= 0.5:
        return vessel['course_deg']
    return None


SCALES = {'closer': 0.48, 'standard': 0.76, 'wider': 1.0}
# The recipe no longer offers a framing choice; every harbor uses this one.
DEFAULT_SCALE = 'standard'


def viewport(port, scale=DEFAULT_SCALE):
    # Wider is the subscribed/collected box. Standard and closer are nested.
    factor = SCALES.get(scale, SCALES[DEFAULT_SCALE])
    w, s, e, n = port['bbox']
    x, y = (w + e) / 2, (s + n) / 2
    return [round(x-(e-w)*factor/2, 6), round(y-(n-s)*factor/2, 6),
            round(x+(e-w)*factor/2, 6), round(y+(n-s)*factor/2, 6)]


def select(vessels, bbox, limit=40):
    """Deterministic round-robin over spatial cells, newest first per cell."""
    cells = {}
    w, s, e, n = bbox
    for v in sorted(vessels, key=lambda v: (-epoch(v['reported_at']), v['mmsi'])):
        if not contains(bbox, v['position']): continue
        x, y = v['position']
        cell = (min(7, int((x-w)/(e-w)*8)), min(5, int((y-s)/(n-s)*6)))
        cells.setdefault(cell, []).append(v)
    result = []
    while cells and len(result) < limit:
        for cell in sorted(list(cells)):
            result.append(cells[cell].pop(0))
            if not cells[cell]: del cells[cell]
            if len(result) == limit: break
    return result
