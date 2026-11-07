import json
from datetime import datetime, timezone
import unittest
from port_of_call.enrichment import Enricher, save_cache
from port_of_call.memory_store import MemoryStore
from port_of_call.model import HARBORS, position
from port_of_call.spotlight import HOLD, choose, knowledge, lookups_worth_making

NOW = 1793811600.0
PORT = HARBORS['helsinki']
RECORD = dict(facts=[dict(label='Builder', value='Meyer Turku'), dict(label='Operator', value='Viking Line'),
                     dict(label='In service', value='2013')],
              built_in=dict(value='Finland'), registry_country=dict(value='Finland'))


def add(store, mid, name, facts, x=0.0, speed=4, now=NOW):
    fx, fy = PORT['focus']
    store.put(position(mid, fx+x, fy, now-30, now, speed=speed),
              dict(mmsi=mid, name=name, updated_at=now-60, type='passenger', facts=facts, facts_source='AIS'))


class Knowledge(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(); self.store.state('last_success', NOW)

    def test_a_ship_record_counts_most(self):
        facts = dict(imo='9606900', length_m=214, beam_m=31, ship_type_code=60, destination='FIHEL')
        add(self.store, '230100001', 'KNOWN', facts)
        add(self.store, '230100002', 'UNKNOWN', {**facts, 'imo': '9606901'}, x=.002)
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        save_cache(self.store, 'ship:9606901', None, NOW, 86400)  # looked up, nothing found
        ships = {v['mmsi']: v for v in self.store.vessels(NOW, 3600, PORT['bbox'])}
        known, unknown = knowledge(self.store, ships['230100001'], NOW), knowledge(self.store, ships['230100002'], NOW)
        self.assertGreater(known, unknown+40)
        # An IMO number not yet looked up still promises more than none at all.
        add(self.store, '230100003', 'PENDING', {**facts, 'imo': '9606902'}, x=.004)
        add(self.store, '230100004', 'NO IMO', {k: v for k, v in facts.items() if k != 'imo'}, x=.006)
        ships = {v['mmsi']: v for v in self.store.vessels(NOW, 3600, PORT['bbox'])}
        self.assertGreater(knowledge(self.store, ships['230100003'], NOW), knowledge(self.store, ships['230100004'], NOW))

    def test_spotlight_picks_the_known_ship_most_of_the_time(self):
        picks = {'KNOWN': 0}
        for window in range(40):
            store = MemoryStore(); now = NOW+window*HOLD; store.state('last_success', now)
            base = dict(length_m=180, beam_m=28, ship_type_code=60, destination='FIHEL')
            add(store, '230200001', 'KNOWN', {**base, 'imo': '9606900'}, now=now)
            for i in range(2, 6):
                add(store, '23020000'+str(i), 'OTHER '+str(i), {**base, 'imo': '960690'+str(i)}, x=i*.002, now=now)
                save_cache(store, 'ship:960690'+str(i), None, now, 86400)
            save_cache(store, 'ship:9606900', RECORD, now, 86400)
            chosen = choose(store, PORT, store.vessels(now, 3600, PORT['bbox']), now)
            if chosen[0]['name'] == 'KNOWN': picks['KNOWN'] += 1
            self.assertEqual(chosen[2] if chosen[0]['name'] == 'KNOWN' else 'Ship record available', 'Ship record available')
        self.assertGreaterEqual(picks['KNOWN'], 24)

    def test_lookahead_is_throttled_and_keeps_a_budget_reserve(self):
        add(self.store, '230300001', 'BIG', dict(imo='9606900', length_m=290, ship_type_code=70))
        add(self.store, '230300002', 'SMALL', dict(imo='9606901', length_m=90, ship_type_code=70), x=.002)
        vessels = self.store.vessels(NOW, 3600, PORT['bbox'])
        self.assertEqual(lookups_worth_making(self.store, PORT, vessels, NOW), ['9606900'])
        clock = [NOW]
        enricher = Enricher(self.store, 'digitraffic', clock=lambda: clock[0])
        enricher.prefetch(PORT['id'], ['9606900']); enricher.prefetch(PORT['id'], ['9606901'])
        self.assertEqual(enricher.queue.qsize(), 1)  # once per port per window
        clock[0] += 3*3600
        self.store.state('wikidata_daily_budget', json.dumps(dict(day=datetime.fromtimestamp(clock[0], timezone.utc).strftime('%Y-%m-%d'), count=300)))
        enricher.prefetch(PORT['id'], ['9606901'])
        self.assertEqual(enricher.queue.qsize(), 1)  # under 250 left today: Spotlight and names keep them
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        self.assertEqual(lookups_worth_making(self.store, PORT, vessels, NOW), ['9606901'])


if __name__ == '__main__':
    unittest.main()
