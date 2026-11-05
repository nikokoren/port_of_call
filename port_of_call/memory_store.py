"""Bounded operational cache for a single edge collector, checkpointed in batches.

Implements the same domain storage methods as Store. No per-message durable
writes: persisting every AIS message would exceed Cloudflare's free SQL quota.
Report and per-field timestamps survive checkpoints without being refreshed.
"""
import copy
import json
from .model import epoch, category
from .facts import VOYAGE, VOYAGE_TTL, IDENTITY_TTL


class MemoryStore:
    def __init__(self, payload=None):
        self.data = json.loads(payload) if payload else {}
        for key in ('positions', 'metadata', 'facts', 'states', 'current', 'history', 'references', 'calls'):
            self.data.setdefault(key, {})

    def put(self, loc=None, static=None):
        if loc:
            old = self.data['positions'].get(loc['mmsi'])
            if not old or epoch(loc['reported_at']) > epoch(old['reported_at']):
                self.data['positions'][loc['mmsi']] = copy.deepcopy(loc)
        if static and static.get('mmsi'):
            mid, ts = static['mmsi'], static['updated_at']
            fields = self.data['facts'].setdefault(mid, {})
            for key, value in static.get('facts', {}).items():
                if key not in fields or ts >= fields[key][0]:
                    fields[key] = [ts, copy.deepcopy(value), static.get('facts_source', 'AIS')]
            old = self.data['metadata'].get(mid, {})
            if ts >= old.get('updated_at', 0):
                if 'type' in old and 'type_updated_at' not in old:
                    old['type_updated_at'] = old.get('updated_at', 0)
                if static.get('type') is not None: old['type_updated_at'] = ts
                old.update({k: copy.deepcopy(v) for k, v in static.items() if v is not None and k not in ('facts', 'facts_source')})
                self.data['metadata'][mid] = old

    def vessels(self, now, ttl):
        result = []
        for mid, loc in self.data['positions'].items():
            if not 0 <= now-epoch(loc['reported_at']) < ttl: continue
            meta = self.data['metadata'].get(mid, {})
            facts = {key: dict(value=copy.deepcopy(value), reported_at=self._iso(ts), source=source)
                     for key, (ts, value, source) in self.data['facts'].get(mid, {}).items()
                     if value is not None and 0 <= now-ts < (VOYAGE_TTL if key in VOYAGE else IDENTITY_TTL)}
            code = facts.get('ship_type_code', {}).get('value')
            vessel = copy.deepcopy(loc)
            vessel.update(name=meta.get('name') if 0 <= now-meta.get('updated_at', 0) < IDENTITY_TTL else None,
                          type=category(code) if code else meta.get('type') if 0 <= now-meta.get('type_updated_at', meta.get('updated_at', 0)) < IDENTITY_TTL else None,
                          facts=facts)
            result.append(vessel)
        return result

    @staticmethod
    def _iso(ts):
        from .model import iso
        return iso(ts)

    def state(self, key, value=None, *, commit=True):
        if value is not None: self.data['states'][key] = str(value)
        return self.data['states'].get(key)

    def current_focus(self, port): return self.data['current'].get(port)
    def focus_history(self, port): return copy.deepcopy(self.data['history'].get(port, {}))

    def save_focus(self, port, mid, now, reason, category):
        self.data['current'][port] = [mid, now, reason]
        history = self.data['history'].setdefault(port, {})
        history[mid] = [now, category]
        self.data['history'][port] = dict(sorted(history.items(), key=lambda row: row[1][0], reverse=True)[:64])

    def reference(self, key, now):
        row = self.data['references'].get(key)
        return (row[0], copy.deepcopy(row[2])) if row and row[1] > now else None

    def save_reference(self, key, payload, now, ttl):
        self.data['references'][key] = [now, now+ttl, copy.deepcopy(payload)]

    def recent_calls(self, now):
        return sorted([(ts, copy.deepcopy(call)) for ts, call in self.data['calls'].values()
                       if 0 <= now-ts < 7*86400], reverse=True, key=lambda row: row[0])

    def save_call(self, key, ts, clean): self.data['calls'][key] = [ts, copy.deepcopy(clean)]
    def commit(self): pass
    def close(self): pass

    def prune(self, now, ttl):
        self.data['positions'] = dict(sorted(
            [(mid, v) for mid, v in self.data['positions'].items() if 0 <= now-epoch(v['reported_at']) < ttl],
            key=lambda row: row[1]['reported_at'], reverse=True)[:5000])
        self.data['metadata'] = dict(sorted(
            [(mid, v) for mid, v in self.data['metadata'].items() if 0 <= now-v['updated_at'] < IDENTITY_TTL],
            key=lambda row: row[1]['updated_at'], reverse=True)[:8000])
        keep = self.data['positions'].keys() | self.data['metadata'].keys()
        self.data['facts'] = {mid: {k: row for k, row in fields.items() if 0 <= now-row[0] < IDENTITY_TTL}
                              for mid, fields in self.data['facts'].items() if mid in keep}
        self.data['references'] = dict(sorted(
            [(k, row) for k, row in self.data['references'].items() if row[1] > now-86400],
            key=lambda row: row[1][0], reverse=True)[:1024])
        self.data['calls'] = dict(sorted(
            [(k, row) for k, row in self.data['calls'].items() if 0 <= now-row[0] < IDENTITY_TTL],
            key=lambda row: row[1][0], reverse=True)[:512])

    def checkpoint(self, now, ttl=3600):
        self.prune(now, ttl)
        def encode(): return json.dumps(self.data, separators=(',', ':'), ensure_ascii=True)
        body = encode()
        # Bound the number of SQL rows/checkpoint. Discard oldest metadata first,
        # never extend freshness or invent a replacement for an evicted fact.
        while len(body) > 8_000_000:
            metadata = self.data['metadata']
            if not metadata: raise ValueError('Checkpoint exceeds bounded storage budget')
            remove = sorted(metadata, key=lambda mid: metadata[mid]['updated_at'])[:max(1, len(metadata)//4)]
            for mid in remove:
                del metadata[mid]
                self.data['facts'].pop(mid, None)
            body = encode()
        return body
