import json
import unittest
from port_of_call.store import Store
from port_of_call.memory_store import MemoryStore
from port_of_call.model import position, HARBORS
from port_of_call.snapshot import snapshot
from port_of_call.enrichment import save_cache

NOW = 1793867309.0


class EdgeStorage(unittest.TestCase):
    def setUp(self): self.sql, self.edge = Store(':memory:'), MemoryStore()
    def tearDown(self): self.sql.close()

    def seed(self, store):
        for i in range(4):
            mid = str(230000001+i)
            store.put(position(mid, 24.95+i*.005, 60.15, NOW-60-i, NOW, speed=i, heading=90))
            store.put(static=dict(mmsi=mid, name='SHIP '+str(i), type='cargo', updated_at=NOW-120,
                facts=dict(destination='PLGDN', length_m=200+i, beam_m=24, imo='9345398', ship_type_code=70), facts_source='AIS'))
        store.state('last_success', NOW)
        save_cache(store, 'mid:230', dict(name='Finland', code='FI', url='https://www.wikidata.org/wiki/Q33'), NOW, 3600)

    def test_same_snapshot_and_stable_spotlight_across_checkpoint(self):
        for store in (self.sql, self.edge): self.seed(store)
        for scale in ('closer', 'standard', 'wider'):
            for focus in (False, True):
                self.assertEqual(snapshot(self.sql, HARBORS['helsinki'], NOW, scale=scale, spotlight=focus),
                                 snapshot(self.edge, HARBORS['helsinki'], NOW, scale=scale, spotlight=focus))
        restored = MemoryStore(self.edge.checkpoint(NOW))
        self.assertEqual(snapshot(self.edge, HARBORS['helsinki'], NOW+60, spotlight=True),
                         snapshot(restored, HARBORS['helsinki'], NOW+60, spotlight=True))
        self.assertEqual(snapshot(restored, HARBORS['helsinki'], NOW+3601)['vessels'], [])

    def test_out_of_order_unknowns_and_independent_expiry_match_sql(self):
        for store in (self.sql, self.edge):
            self.seed(store)
            store.put(position('230000001', 25.0, 60.15, NOW-200, NOW))
            store.put(static=dict(mmsi='230000001', updated_at=NOW-180, facts={'destination': 'OLD'}))
            store.put(static=dict(mmsi='230000001', updated_at=NOW-10, facts={'destination': None}))
        for now in (NOW, NOW+3601, NOW+7*86400):
            self.assertEqual(sorted(self.sql.vessels(now, 86400), key=lambda v: v['mmsi']),
                             sorted(self.edge.vessels(now, 86400), key=lambda v: v['mmsi']))

    def test_reference_negative_cache_budget_and_call_provenance_survive(self):
        self.edge.save_reference('missing', None, NOW, 60)
        self.edge.state('wikidata_daily_budget', json.dumps({'day': '2026-11-05', 'count': 500}))
        clean = dict(port='FIHEL', mmsi='230000001', previous='FIRAU', ata=NOW-100, atd=None, imo=None, nationality='FI')
        self.edge.save_call('one', NOW-10, clean)
        restored = MemoryStore(self.edge.checkpoint(NOW))
        self.assertEqual(restored.reference('missing', NOW), (NOW, None))
        self.assertIsNone(restored.reference('missing', NOW+60))
        self.assertEqual(restored.recent_calls(NOW), [(NOW-10, clean)])
        self.assertEqual(json.loads(restored.state('wikidata_daily_budget'))['count'], 500)

    def test_bounded_checkpoint_retains_original_report_times(self):
        self.seed(self.edge)
        before = self.edge.vessels(NOW, 3600)
        body = self.edge.checkpoint(NOW+30)
        self.assertLessEqual(len(body), 8_000_000)
        after = MemoryStore(body).vessels(NOW+30, 3600)
        self.assertEqual([v['reported_at'] for v in before], [v['reported_at'] for v in after])
        self.assertEqual(self.edge.data['positions']['230000001']['position'], [24.95, 60.15])

    def test_area_filter_matches_sql_and_snapshots_only_load_their_harbor(self):
        for store in (self.sql, self.edge):
            self.seed(store)
            # A ship in another harbor must not be loaded for a Helsinki snapshot.
            store.put(position('244000001', 4.1, 51.95, NOW-30, NOW))
        box = HARBORS['helsinki']['bbox']
        for store in (self.sql, self.edge):
            ids = sorted(v['mmsi'] for v in store.vessels(NOW, 3600, box))
            self.assertEqual(ids, ['230000001', '230000002', '230000003', '230000004'])
            self.assertEqual(len(store.vessels(NOW, 3600)), 5)
        self.assertEqual(self.sql.vessels(NOW, 3600, box), self.edge.vessels(NOW, 3600, box))
        seen = []
        original = self.edge.vessels
        def spy(now, ttl, bbox=None):
            seen.append(bbox); return original(now, ttl, bbox)
        self.edge.vessels = spy
        snapshot(self.edge, HARBORS['helsinki'], NOW, spotlight=True)
        self.assertTrue(seen and all(b == box for b in seen), seen)
