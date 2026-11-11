import unittest
from port_of_call.destination_terms import describe, ACTIVITIES, ROUTES, PORT_REFERENCES
from port_of_call.display import label_voyage, focus_copy
from port_of_call.enrichment import enrich_card, resolve_port, Enricher
from port_of_call.memory_store import MemoryStore
from port_of_call.model import HARBORS, position
from port_of_call.snapshot import snapshot

NOW = 1793811600.0


class Terms(unittest.TestCase):
    def test_wsf_round_trip_has_human_names_without_claiming_direction_or_operator(self):
        for raw in ['WSFSWUSSEAWSFSW', 'wsfsw ussea wsfsw', 'WSFSW-USSEA-WSFSW']:
            term=describe(raw)
            self.assertEqual(term['text'],'Southworth ↔ Seattle, USA')
            self.assertTrue(term['inferred']);self.assertFalse(term['direction_known'])
            context=dict(destination=dict(value=raw),origin=dict(value='A previous port'))
            self.assertEqual(label_voyage(context),'Likely route: Southworth ↔ Seattle, USA')
            self.assertEqual(focus_copy(context)['journey']['label'],'Likely route')
            self.assertEqual(context['destination']['value'],raw)

    def test_known_routes_and_activities_render_as_notes_not_destination_ports(self):
        for raw in list(ROUTES)+list(ACTIVITIES)+['WSF','FOR SALE']:
            term=describe(raw)
            self.assertIsNotNone(term)
            self.assertTrue(term['source_url'].startswith('https://'))
            self.assertFalse(label_voyage(dict(destination=dict(value=raw))).startswith('To '))
            self.assertIsNone(resolve_port(MemoryStore(),raw,NOW))
        self.assertEqual(label_voyage(dict(destination=dict(value='PIER 50 / W SEATTLE'))),
            'Route: Seattle Pier 50 ↔ West Seattle, USA')
        self.assertEqual(label_voyage(dict(destination=dict(value='SAR TURKU AREA'))),
            'Activity: Search and rescue in the Turku area')

    def test_unreviewed_operator_codes_are_not_guessed(self):
        for raw in ['WSFUNKNOWN', 'WSFSWUSLAXWSFSW', 'VLA-IMM-VLA', 'AEBA', 'ABOSJALONAGU', None]:
            self.assertIsNone(describe(raw))

    def test_metadata_preserves_raw_value_and_source_without_relabeling_origin(self):
        focus=dict(mmsi='230000001',imo=None,reported_at='2026-11-04T17:00:00Z',
            destination=dict(value='WSFSWUSSEAWSFSW'),origin=None)
        enrich_card(MemoryStore(),HARBORS['seattle'],focus,NOW,calls=[])
        self.assertIsNone(focus['origin']);self.assertIsNone(focus['destination_port'])
        self.assertTrue(focus['destination_term']['inferred'])
        self.assertEqual(focus['destination']['value'],'WSFSWUSSEAWSFSW')

    def test_known_nonport_terms_do_not_waste_port_lookup_budget(self):
        store=MemoryStore();store.state('last_success',NOW)
        port=HARBORS['helsinki'];x,y=port['focus']
        for i,raw in enumerate(['TRIAL','WSFSWUSSEAWSFSW','FAIRWAY WORK']):
            mid=str(230100001+i)
            store.put(position(mid,x+i*.001,y,NOW-30,NOW,speed=2),
                dict(mmsi=mid,name='TEST SHIP',updated_at=NOW,facts=dict(destination=raw,length_m=50)))
        data=snapshot(store,port,NOW)
        self.assertEqual(data['unresolved_ports'],[])
        self.assertTrue(any(v.get('voyage','').startswith('Likely route:') for v in data['vessels']))
        e=Enricher(store,'aisstream',clock=lambda:NOW)
        e.enqueue(dict(destination=dict(value='TRIAL')))
        self.assertEqual(e.queue.qsize(),0)

    def test_reviewed_port_entities_resolve_duplicate_city_port_records(self):
        for code,(name,country,qid) in PORT_REFERENCES.items():
            ref=resolve_port(MemoryStore(),code,NOW)
            self.assertEqual(ref['name'],name);self.assertEqual(ref['country'],country)
            self.assertTrue(ref['url'].endswith('/'+qid));self.assertNotIn('position',ref)
