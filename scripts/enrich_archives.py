"""Refresh free reference metadata for Spotlight archives without changing AIS observations."""
import asyncio
import json
import time
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout
from port_of_call.enrichment import Enricher, enrich_card
from port_of_call.facts import infer_eta
from port_of_call.display import focus_copy
from port_of_call.model import HARBORS, epoch, iso
from port_of_call.store import Store

async def run():
    store = Store('var/spotlight-capture.sqlite3')
    enricher = Enricher(store, 'digitraffic')
    async with ClientSession(trust_env=True, timeout=ClientTimeout(total=30)) as session:
        for key in ('helsinki','turku','rauma'):
            path = Path('fixtures/'+key+'-spotlight.json')
            data = json.loads(path.read_text())
            focus = data.get('focus')
            if not focus: continue
            # Existing sanitized call records support the historical visit. No
            # position is collected, replayed, re-dated or moved by this helper.
            focus.update(flag=None, built_in=None, enrichment=None)
            enricher.enqueue(focus)
            while not enricher.queue.empty():
                kind, identifier = enricher.queue.get_nowait()
                await enricher.refresh(session, kind, identifier)
                enricher.pending.discard(kind+':'+identifier)
                enricher.queue.task_done()
            enrich_card(store, HARBORS[key], focus, time.time())
            focus['eta_estimate'] = infer_eta(focus.get('eta'), epoch(data['snapshot_at']))
            focus['presentation'] = focus_copy(focus)
            data['reference_enriched_at'] = iso(time.time())
            data['fixture_note'] = 'Genuine historical AIS observations; NOT current traffic. Free reference facts retrieved at reference_enriched_at; position/report times unchanged.'
            path.write_text(json.dumps(data, indent=2)+'\n')
            print(key, 'destination', focus.get('destination_port'), 'flag', focus.get('flag'), 'built', focus.get('built_in'), flush=True)
    store.close()

if __name__ == '__main__': asyncio.run(run())
