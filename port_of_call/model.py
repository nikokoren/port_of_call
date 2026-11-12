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
# The recipe no longer offers a framing choice. Every harbor is shown around its
# curated focus at its own reviewed map zoom (registry `zoom`, chosen per port
# in the view editor; 11 when absent). The extent is what that zoom shows on an
# 800x480 screen.
DEFAULT_SCALE = 'harbor'
HARBOR_ZOOM = 11


def harbor_camera(port, device='og'):
    profile = port.get('cameras', {}).get(device, {})
    return dict(center=list(profile.get('focus') or port.get('focus') or port['center']),
                zoom=profile.get('zoom', port.get('zoom', HARBOR_ZOOM)))


def harbor_zoom(port, device='og'):
    return port.get('cameras',{}).get(device,{}).get('zoom',port.get('zoom',HARBOR_ZOOM))
HARBOR_VIEW_PX = (800, 480)
DEVICE_VIEW_PX = {'og': HARBOR_VIEW_PX, 'x': (1040, 780)}


def harbor_view(port, device='og'):
    # MapLibre uses 512px tiles: 2**zoom * 512 px span 360 degrees of longitude.
    camera = harbor_camera(port, device)
    lon, lat = camera['center']
    world = 512 * 2 ** camera['zoom']
    width,height = DEVICE_VIEW_PX[device]
    def merc(y): return math.log(math.tan(math.pi/4 + math.radians(y)/2))
    def unmerc(m): return math.degrees(2*math.atan(math.exp(m)) - math.pi/2)
    dx = 360 * width / 2 / world
    dm = 2 * math.pi * height / 2 / world
    return [round(lon-dx, 6), round(unmerc(merc(lat)-dm), 6), round(lon+dx, 6), round(unmerc(merc(lat)+dm), 6)]


def viewport(port, scale=DEFAULT_SCALE):
    if scale == 'harbor': return harbor_view(port)
    # Wider is the subscribed/collected box. Standard and closer are nested.
    factor = SCALES.get(scale, SCALES['standard'])
    w, s, e, n = port['bbox']
    x, y = (w + e) / 2, (s + n) / 2
    return [round(x-(e-w)*factor/2, 6), round(y-(n-s)*factor/2, 6),
            round(x+(e-w)*factor/2, 6), round(y+(n-s)*factor/2, 6)]


def map_candidates_view(port, core, device='og'):
    """Cover portrait/X and card offsets without changing the reviewed camera.

    A 1400-square logical-pixel envelope covers standard recipe canvases plus
    their information-card offsets. Only positions inside source coverage enter.
    """
    x,y = harbor_camera(port,device)['center']
    width,height = DEVICE_VIEW_PX[device]
    dx = (core[2]-core[0])*1400/width/2
    dy = (core[3]-core[1])*1400/height/2
    w,s,e,n = port['bbox']
    return [max(w,x-dx),max(s,y-dy),min(e,x+dx),min(n,y+dy)]


def union_view(boxes):
    return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]


def select_views(vessels, boxes, limit, key=None):
    """Alternate spatial queues so either approved device view can contribute."""
    queues = [iter(select(vessels,box,limit,key=key)) for box in boxes]
    result,seen = [],set()
    while queues and len(result)<limit:
        active = []
        for queue in queues:
            for vessel in queue:
                if vessel['mmsi'] not in seen:
                    seen.add(vessel['mmsi']);result.append(vessel);break
            else: continue
            active.append(queue)
            if len(result)==limit: break
        queues=active
    return result


def select(vessels, bbox, limit=40, key=None):
    """Deterministic round-robin over spatial cells.

    Within a cell the highest key comes first (newest first by default), so
    every part of the view stays represented while busy cells send their
    most interesting ships.
    """
    cells = {}
    w, s, e, n = bbox
    order = (lambda v: (-key(v), -epoch(v['reported_at']), v['mmsi'])) if key else (lambda v: (-epoch(v['reported_at']), v['mmsi']))
    for v in sorted(vessels, key=order):
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
