import json
import sqlite3
from pathlib import Path
from .model import epoch, iso, category
from .facts import VOYAGE, VOYAGE_TTL, IDENTITY_TTL


class Store:
    def __init__(self, path):
        if path != ':memory:': Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS positions (mmsi TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS metadata (mmsi TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS vessel_facts (mmsi TEXT, field TEXT, ts REAL, value TEXT, source TEXT, PRIMARY KEY(mmsi,field));
        CREATE TABLE IF NOT EXISTS focus_current (port TEXT PRIMARY KEY, mmsi TEXT, selected_at REAL, reason TEXT);
        CREATE TABLE IF NOT EXISTS focus_history (port TEXT, mmsi TEXT, ts REAL, category TEXT, PRIMARY KEY(port,mmsi));
        CREATE TABLE IF NOT EXISTS enrichment (key TEXT PRIMARY KEY, ts REAL, expires REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS port_calls (id TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
        ''')

    def put(self, loc=None, static=None):
        if loc:
            self.db.execute('''INSERT INTO positions VALUES (?,?,?) ON CONFLICT(mmsi) DO UPDATE
                SET ts=excluded.ts,payload=excluded.payload WHERE excluded.ts>positions.ts''',
                (loc['mmsi'], epoch(loc['reported_at']), json.dumps(loc)))
        if static and static.get('mmsi'):
            for field, value in static.get('facts', {}).items():
                self.db.execute('''INSERT INTO vessel_facts VALUES (?,?,?,?,?) ON CONFLICT(mmsi,field) DO UPDATE
                    SET ts=excluded.ts,value=excluded.value,source=excluded.source WHERE excluded.ts>=vessel_facts.ts''',
                    (static['mmsi'], field, static['updated_at'], json.dumps(value), static.get('facts_source', 'AIS')))
            row = self.db.execute('SELECT ts,payload FROM metadata WHERE mmsi=?', (static['mmsi'],)).fetchone()
            if not row or static['updated_at'] >= row[0]:
                merged = json.loads(row[1]) if row else {}
                if 'type' in merged and 'type_updated_at' not in merged:
                    merged['type_updated_at'] = merged.get('updated_at', 0)
                if static.get('type') is not None: merged['type_updated_at'] = static['updated_at']
                merged.update({k: v for k, v in static.items() if v is not None and k not in ('facts', 'facts_source')})
                self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?,?)',
                                (static['mmsi'], static['updated_at'], json.dumps(merged)))

    def commit(self): self.db.commit()

    def state(self, key, value=None, *, commit=True):
        if value is not None:
            self.db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (key, str(value)))
            if commit: self.db.commit()
        row = self.db.execute('SELECT value FROM state WHERE key=?', (key,)).fetchone()
        return row[0] if row else None

    def prune(self, now, ttl):
        self.db.execute('DELETE FROM positions WHERE ts<=?', (now-ttl,))
        self.db.execute('DELETE FROM metadata WHERE ts<?', (now-86400*7,))
        self.db.execute('DELETE FROM vessel_facts WHERE ts<?', (now-IDENTITY_TTL,))
        self.db.execute('DELETE FROM enrichment WHERE expires<?', (now-86400,))
        self.db.execute('DELETE FROM port_calls WHERE ts<?', (now-7*86400,))
        self.db.commit()

    def vessels(self, now, ttl):
        rows = self.db.execute('''SELECT p.payload,m.payload FROM positions p
            LEFT JOIN metadata m ON p.mmsi=m.mmsi WHERE p.ts>? AND p.ts<=?''', (now-ttl, now))
        facts = {}
        for mid, field, ts, value, source in self.db.execute('SELECT * FROM vessel_facts WHERE ts>? AND ts<=?', (now-IDENTITY_TTL, now)):
            if now-ts < (VOYAGE_TTL if field in VOYAGE else IDENTITY_TTL):
                val = json.loads(value)
                if val is not None: facts.setdefault(mid, {})[field] = dict(value=val, reported_at=iso(ts), source=source)
        result = []
        for p, m in rows:
            vessel = json.loads(p)
            # Metadata expires independently and never refreshes a position.
            meta = json.loads(m) if m else {}
            recent = now-meta.get('updated_at', 0) < 7*86400
            type_recent = 0 <= now-meta.get('type_updated_at', meta.get('updated_at', 0)) < IDENTITY_TTL
            code = facts.get(vessel['mmsi'], {}).get('ship_type_code', {}).get('value')
            vessel.update(name=meta.get('name') if recent else None,
                          type=category(code) if code else meta.get('type') if type_recent else None)
            vessel['facts'] = facts.get(vessel['mmsi'], {})
            result.append(vessel)
        return result

    def close(self): self.db.close()

    def current_focus(self, port):
        return self.db.execute('SELECT mmsi,selected_at,reason FROM focus_current WHERE port=?', (port,)).fetchone()

    def focus_history(self, port):
        return {mid: (ts, category) for mid, ts, category in self.db.execute(
            'SELECT mmsi,ts,category FROM focus_history WHERE port=?', (port,))}

    def save_focus(self, port, mid, now, reason, category):
        self.db.execute('INSERT OR REPLACE INTO focus_current VALUES (?,?,?,?)', (port, mid, now, reason))
        self.db.execute('INSERT OR REPLACE INTO focus_history VALUES (?,?,?,?)', (port, mid, now, category))
        self.db.execute('DELETE FROM focus_history WHERE port=? AND mmsi NOT IN (SELECT mmsi FROM focus_history WHERE port=? ORDER BY ts DESC LIMIT 64)', (port, port))
        self.commit()

    def reference(self, key, now):
        row = self.db.execute('SELECT ts,payload FROM enrichment WHERE key=? AND expires>?', (key, now)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def save_reference(self, key, payload, now, ttl):
        self.db.execute('INSERT OR REPLACE INTO enrichment VALUES (?,?,?,?)', (key, now, now+ttl, json.dumps(payload)))
        self.commit()

    def recent_calls(self, now):
        return [(ts, json.loads(payload)) for ts, payload in self.db.execute(
            'SELECT ts,payload FROM port_calls WHERE ts>? AND ts<=? ORDER BY ts DESC', (now-7*86400, now))]

    def save_call(self, key, ts, clean):
        self.db.execute('INSERT OR REPLACE INTO port_calls VALUES (?,?,?)', (key, ts, json.dumps(clean)))
