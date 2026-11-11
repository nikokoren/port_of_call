"""Small history of real AIS fixes; never interpolate or extrapolate positions."""
import math
from .model import epoch, iso

WINDOW, INTERVAL, POINTS, VESSELS = 1800, 120, 12, 600


def distance(a, b):
    x, y = map(math.radians, a); xx, yy = map(math.radians, b)
    h = math.sin((yy-y)/2)**2 + math.cos(y)*math.cos(yy)*math.sin((xx-x)/2)**2
    return 3440.065 * 2 * math.asin(min(1, math.sqrt(h)))


def append(points, loc):
    ts = epoch(loc['reported_at'])
    points = [p for p in points if 0 <= ts-p[0] <= WINDOW]
    if (loc.get('speed_knots') or 0) < 1: return points
    point = [ts, *loc['position']]
    if points:
        dt = ts-points[-1][0]
        if dt <= 0: return points
        miles = distance(points[-1][1:], point[1:])
        if dt > 360 or miles > 65*dt/3600 + .1: return [point]
        if dt < INTERVAL or miles < .025: return points
    return (points+[point])[-POINTS:]


def trail(points, loc, now):
    points = [p for p in points if 0 <= now-p[0] <= WINDOW]
    ts = epoch(loc['reported_at'])
    if points and ts > points[-1][0]:
        dt = ts-points[-1][0]
        if dt > 360 or distance(points[-1][1:], loc['position']) > 65*dt/3600+.1: return []
        points = (points+[[ts, *loc['position']]])[-POINTS:]
    if len(points) < 2: return []
    return [dict(position=[round(p[1],5),round(p[2],5)], reported_at=iso(p[0])) for p in points]
