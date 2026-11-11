"""Bounded aggregate review queue for opaque terms actually used by map labels."""
import json
import re
from .destinations import parse
from .destination_terms import describe

KEY, RETENTION = 'destination_review_v1', 7*86400


def record_many(store, port, contexts, now):
    data = None
    for context in contexts:
        raw = (context.get('destination') or {}).get('value')
        if not raw or context.get('destination_port') or describe(raw): continue
        raw = ' '.join(str(raw).upper().split())[:48]
        if not raw or not re.fullmatch(r'[A-Z0-9 /&_.:>\-]+',raw): continue
        if data is None: data = json.loads(store.state(KEY) or '{}')
        rows = data.setdefault(port,{})
        row = rows.setdefault(raw,dict(first_seen=now,last_seen=now,windows=0,ships=[]))
        slot = int(now//1800)
        if row.get('slot')!=slot: row['windows']+=1;row['slot']=slot
        row['last_seen']=now
        mid = context.get('mmsi')
        if mid and mid not in row['ships']: row['ships']=(row['ships']+[mid])[-64:]
    if data is None:return
    data[port] = dict(sorted(((k,v) for k,v in rows.items() if now-v['last_seen']<RETENTION),
        key=lambda r:(len(r[1]['ships']),r[1]['windows'],r[1]['last_seen']),reverse=True)[:32])
    store.state(KEY,json.dumps(data,separators=(',',':')))


def report(store, now):
    rows=[]
    for port,terms in json.loads(store.state(KEY) or '{}').items():
        for term,row in terms.items():
            if now-row['last_seen']>=RETENTION:continue
            rows.append(dict(port=port,term=term,vessels=len(row['ships']),windows=row['windows'],last_seen=row['last_seen']))
    return dict(window_days=7,terms=sorted(rows,key=lambda r:(-r['vessels'],-r['windows'],r['port'],r['term'])))
