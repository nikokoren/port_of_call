import json
import unittest
from port_of_call.port_facts import FACTS, port_fact
from port_of_call.model import HARBORS
from port_of_call.enrichment import resolve_port
from port_of_call.store import Store
from port_of_call.payload import encode_snapshot


class PortFacts(unittest.TestCase):
    def test_collections_cover_verified_ports_with_short_sourced_facts(self):
        for port in HARBORS.values():
            if not port.get('verified'): continue
            facts=FACTS[port['id']]
            self.assertGreaterEqual(len(facts),2)
            self.assertEqual(len(facts),len({text for text,url in facts}))
            for text,url in facts:
                self.assertLessEqual(len(text),100)
                self.assertTrue(url.startswith('https://'))
                self.assertNotIn('<',text)

    def test_hourly_rotation_is_stable_and_visits_entire_collection(self):
        for key, collection in FACTS.items():
            first=port_fact(key,3600)
            self.assertEqual(first,port_fact(key,7199))
            self.assertEqual(len({port_fact(key,h*3600)['id'] for h in range(len(collection))}),len(collection))
            self.assertEqual(first,port_fact(key,(1+len(collection))*3600))
        self.assertIsNone(port_fact('unsupported',3600))

    def test_mersrags_code_resolves_without_guessing_position(self):
        store=Store(':memory:')
        try:
            result=resolve_port(store,'LVMRX',3600)
            self.assertEqual(result['name'],'Mērsrags')
            self.assertEqual(result['country'],'Latvia')
            self.assertNotIn('position',result)
        finally:store.close()

    def test_optional_blurb_is_dropped_before_positions_under_payload_pressure(self):
        data=dict(vessels=[dict(mmsi='230000001',position=[25,60])],shown=1,total=1,omitted=0,
                  port_fact=dict(text='x'*15000))
        result=json.loads(encode_snapshot(data))
        self.assertNotIn('port_fact',result)
        self.assertEqual(result['vessels'],data['vessels'])
