import json
import sqlite3
from pathlib import Path
from .model import epoch


class Store:
    def __init__(self, path):
        if path != ':memory:': Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS positions (mmsi TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS metadata (mmsi TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
        ''')

    def put(self, loc=None, static=None):
        if loc:
            self.db.execute('''INSERT INTO positions VALUES (?,?,?) ON CONFLICT(mmsi) DO UPDATE
                SET ts=excluded.ts,payload=excluded.payload WHERE excluded.ts>positions.ts''',
                (loc['mmsi'], epoch(loc['reported_at']), json.dumps(loc)))
        if static and static.get('mmsi'):
            row = self.db.execute('SELECT ts,payload FROM metadata WHERE mmsi=?', (static['mmsi'],)).fetchone()
            if not row or static['updated_at'] >= row[0]:
                merged = json.loads(row[1]) if row else {}
                merged.update({k: v for k, v in static.items() if v is not None})
                self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?,?)',
                                (static['mmsi'], static['updated_at'], json.dumps(merged)))

    def commit(self): self.db.commit()

    def state(self, key, value=None):
        if value is not None:
            self.db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (key, str(value)))
            self.db.commit()
        row = self.db.execute('SELECT value FROM state WHERE key=?', (key,)).fetchone()
        return row[0] if row else None

    def prune(self, now, ttl):
        self.db.execute('DELETE FROM positions WHERE ts<=?', (now-ttl,))
        self.db.execute('DELETE FROM metadata WHERE ts<?', (now-86400*7,))
        self.db.commit()

    def vessels(self, now, ttl):
        rows = self.db.execute('''SELECT p.payload,m.payload FROM positions p
            LEFT JOIN metadata m ON p.mmsi=m.mmsi WHERE p.ts>? AND p.ts<=?''', (now-ttl, now))
        result = []
        for p, m in rows:
            vessel = json.loads(p)
            # Metadata expires independently and never refreshes a position.
            meta = json.loads(m) if m else {}
            recent = now-meta.get('updated_at', 0) < 7*86400
            vessel.update(name=meta.get('name') if recent else None, type=meta.get('type') if recent else None)
            result.append(vessel)
        return result

    def close(self): self.db.close()
