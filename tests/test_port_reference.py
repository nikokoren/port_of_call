import unittest
from unittest.mock import AsyncMock
from port_of_call._locode_data import DATA, COUNT
from port_of_call.port_reference import lookup
from port_of_call.enrichment import Enricher, resolve_port, cached
from port_of_call.memory_store import MemoryStore

NOW = 1793811600.0


def entity(name, coordinates=None, classes=None):
    result = dict(id='Q9', labels={'en': {'value': name}}, claims={})
    if coordinates is not None:
        result['claims']['P625'] = [dict(mainsnak=dict(snaktype='value', datavalue=dict(value=c))) for c in coordinates]
    if classes:
        result['claims']['P31'] = [dict(mainsnak=dict(snaktype='value', datavalue=dict(value={'id': c}))) for c in classes]
    return result


class Reference(unittest.TestCase):
    def test_exact_index_round_trips_all_names_without_destination_coordinates(self):
        rows = DATA.splitlines()
        self.assertEqual(len(rows), COUNT)
        self.assertGreater(COUNT, 40000)
        codes = []
        for row in rows:
            code, qid, name = row.split('\t', 2)
            codes.append(code)
            record = lookup(code)
            self.assertEqual(record['name'], name)
            self.assertTrue(record['url'].endswith('/'+qid))
            self.assertNotIn('position', record)
        self.assertEqual(codes, sorted(set(codes)))

    def test_real_names_unknown_codes_and_mutation_safety(self):
        store = MemoryStore()
        for code, name in [('JPKRE', 'Kure'), ('USORF', 'Norfolk'), ('DEBRB', 'Brunsbüttel'), ('GBIMM', 'Immingham')]:
            self.assertEqual(resolve_port(store, code, NOW)['name'], name)
        self.assertIsNone(lookup('ZAQQQ'))
        self.assertIsNone(lookup('ZZZZZ'))
        item = lookup('USORF'); item['name'] = 'Changed'
        self.assertEqual(lookup('USORF')['name'], 'Norfolk')
        # CNSHA's only Wikidata match in this snapshot is an airport, excluded.
        self.assertIsNone(lookup('CNSHA'))

    def test_bundled_names_do_not_queue_external_requests(self):
        enricher = Enricher(MemoryStore(), 'aisstream', clock=lambda: NOW)
        enricher.enqueue_ports(['USORF', 'DEBRB', 'GBIMM', 'ZAQQQ'])
        self.assertEqual(enricher.queue.qsize(), 1)
        self.assertEqual(enricher.queue.get_nowait(), ('port', 'ZA QQQ'))


class NameOnlyLookups(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.e = Enricher(self.store, 'aisstream', clock=lambda: NOW)

    async def test_verified_name_survives_missing_invalid_or_ambiguous_coordinates(self):
        for coords in [None, [], [None],
                       [dict(globe='moon', longitude=1, latitude=1)],
                       [dict(globe='http://www.wikidata.org/entity/Q2', longitude=1, latitude=1),
                        dict(globe='http://www.wikidata.org/entity/Q2', longitude=2, latitude=2)]]:
            self.store.data['references'].clear()
            self.e.lookup = AsyncMock(return_value=entity('Verified name', coords))
            result = await self.e.refresh(None, 'port', 'ZA QQQ')
            self.assertEqual(result['name'], 'Verified name')
            self.assertNotIn('position', result)

    async def test_old_coordinate_required_miss_is_retried_but_other_caches_survive(self):
        self.store.save_reference('v2:port:ZA QQQ', None, NOW, 7*86400)
        self.store.save_reference('v2:ship:9000001', {'facts': []}, NOW, 30*86400)
        self.e.lookup = AsyncMock(return_value=entity('Name without coordinates'))
        self.e.enqueue_ports(['ZAQQQ'])
        await self.e.process_next(None)
        self.assertEqual(resolve_port(self.store, 'ZAQQQ', NOW)['name'], 'Name without coordinates')
        self.assertIsNotNone(cached(self.store, 'ship:9000001', NOW))

    async def test_airport_matches_are_never_promoted_to_ship_destinations(self):
        for name, classes in [('Some International Airport', None), ('LaGuardia', ['Q1248784'])]:
            self.store.data['references'].clear()
            self.e.lookup = AsyncMock(return_value=entity(name, classes=classes))
            self.assertIsNone(await self.e.refresh(None, 'port', 'ZA QQQ'))
        self.store.save_reference('v2:port:CN SHA', {'name': 'Shanghai Hongqiao International Airport'}, NOW, 30*86400)
        self.assertIsNone(resolve_port(self.store, 'CNSHA', NOW))
