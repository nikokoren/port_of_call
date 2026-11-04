"""Synthetic positions: only ever served by the opt-in /demo/ endpoint."""
import random
from .store import Store
from .model import position


def demo_store(port, now):
    store = Store(':memory:')
    rng = random.Random(42)
    w,s,e,n = port['bbox']
    for i in range(120):
        mid = str(900000001+i)
        loc = position(mid, rng.uniform(w,e), rng.uniform(s,n), now-120-i, now,
                       heading=rng.randrange(360), speed=5, course=90)
        store.put(loc, dict(mmsi=mid, name=f'DEMO {i+1:03}', type='cargo', updated_at=now))
    store.state('last_success',now)
    return store
