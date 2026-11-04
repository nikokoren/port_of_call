"""One real snapshot collection. No secrets; preserve original observation times."""
import asyncio
import json
import time
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout
from port_of_call.app import Config
from port_of_call.collector import Collector
from port_of_call.model import HARBORS, epoch, contains
from port_of_call.snapshot import snapshot
from port_of_call.store import Store

async def run():
    store = Store('var/capture.sqlite3')
    collector = Collector(store, Config())
    async with ClientSession(trust_env=True,timeout=ClientTimeout(total=60)) as session:
        await collector.poll(session)
    now=time.time()
    for port in HARBORS.values():
        if port['provider'] != 'digitraffic': continue
        data=snapshot(store,port,now,scale='wider')
        # Historical fixtures are explicitly identified and never served by public API.
        data['fixture_note']='Genuine historical AIS capture; NOT current traffic. See snapshot_at.'
        Path('fixtures/'+port['id']+'.json').write_text(json.dumps(data,indent=2)+'\n')
        print(port['name'],data['status'],data['total'],'vessels',data['snapshot_at'])
    Path('fixtures/capture-metrics.json').write_text(json.dumps({
        'captured_at':data['snapshot_at'], 'accepted':collector.accepted,'rejected':collector.rejected,
        'harbors':[{ 'id':h['id'], 'vessels':len(vs := [v for v in store.vessels(now,3600)
                      if contains(h['bbox'],v['position'])]),
                     'names':sum(bool(v['name']) for v in vs),
                     'headings':sum(v['heading_deg'] is not None for v in vs),
                     'courses':sum(v['course_deg'] is not None for v in vs),
                     'types':sum(v['type'] is not None for v in vs),
                     'fresh_30min':sum(now-epoch(v['reported_at'])<1800 for v in vs)}
                   for h in HARBORS.values() if h['provider']=='digitraffic']},indent=2)+'\n')
    store.close()

asyncio.run(run())
