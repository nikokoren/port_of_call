"""Capture real free-source Spotlight examples, with original timestamps and archive labels."""
import asyncio
import json
import time
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout
from port_of_call.app import Config
from port_of_call.collector import Collector
from port_of_call.enrichment import Enricher
from port_of_call.model import HARBORS, contains
from port_of_call.snapshot import snapshot
from port_of_call.store import Store
from port_of_call.spotlight import eligible

async def run():
    store = Store('var/spotlight-capture.sqlite3')
    collector = Collector(store, Config())
    enricher = Enricher(store, 'digitraffic')
    async with ClientSession(trust_env=True, timeout=ClientTimeout(total=60)) as session:
        await collector.poll(session)
        await enricher.portnet(session)
        now = time.time()
        metrics = {'captured_at': now, 'source': 'Fintraffic / Digitraffic · CC BY 4.0', 'harbors': []}
        for port in HARBORS.values():
            if port['provider'] != 'digitraffic': continue
            data = snapshot(store, port, now, scale='wider', spotlight=True)
            focus = data['focus']
            if focus:
                if focus.get('imo'): await enricher.refresh(session, 'ship', focus['imo'])
                enricher.enqueue(focus)
                while not enricher.queue.empty():
                    kind, key = enricher.queue.get_nowait()
                    await enricher.refresh(session, kind, key)
                    enricher.queue.task_done()
            data = snapshot(store, port, now, scale='wider', spotlight=True)
            data['fixture_note'] = 'Genuine historical free-source capture; NOT current traffic. Original report timestamps preserved.'
            Path('fixtures/'+port['id']+'-spotlight.json').write_text(json.dumps(data, indent=2)+'\n')
            vs = [v for v in store.vessels(now, 3600) if contains(port['bbox'], v['position'])]
            keys = ['imo', 'destination', 'eta', 'length_m', 'beam_m', 'draught_m', 'call_sign']
            metrics['harbors'].append(dict(id=port['id'], observations=len(vs), eligible=sum(eligible(v, now) for v in vs),
                                           fields={k: sum(k in v['facts'] for v in vs) for k in keys}, spotlight=bool(data['focus'])))
            print(port['id'], 'eligible', metrics['harbors'][-1]['eligible'], 'featured', data['focus']['name'] if data['focus'] else None)
        Path('fixtures/spotlight-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    store.close()

if __name__ == '__main__': asyncio.run(run())
