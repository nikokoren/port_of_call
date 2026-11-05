import json
import unittest
from port_of_call.display import label_voyage
from port_of_call.model import HARBORS, position
from port_of_call.store import Store
from port_of_call.snapshot import snapshot
from port_of_call.payload import encode_snapshot

NOW = 1793867309.0


class VoyageLabels(unittest.TestCase):
    def test_known_voyage_uses_resolved_places_and_country_codes(self):
        context = dict(origin=dict(value='Port of Hanko',country='Finland',code='FIHKO'),
                       destination=dict(value='GBTIL'), destination_port=dict(name='Port of Tilbury',country='United Kingdom',code='GBTIL'))
        self.assertEqual(label_voyage(context),'Hanko, FI → Tilbury, GB')
        context['origin']=None
        self.assertEqual(label_voyage(context),'To Tilbury, GB')

    def test_missing_or_cleared_destination_never_leaks_a_cached_route(self):
        self.assertIsNone(label_voyage({}))
        context=dict(destination=None,destination_port=dict(name='Old destination'))
        self.assertIsNone(label_voyage(context))
        context['origin']=dict(value='Hanko',country='Finland')
        self.assertEqual(label_voyage(context),'From Hanko, Finland')

    def test_overview_and_spotlight_markers_share_truthful_cached_voyages(self):
        store=Store(':memory:')
        try:
            for i in (1,2):
                mid=str(230000000+i)
                store.put(position(mid,24.95+i*.01,60.15,NOW-30,NOW,speed=4))
                store.put(static=dict(mmsi=mid,name='SHIP '+str(i),updated_at=NOW-60,
                                      facts=dict(destination='NLRTM',length_m=180)))
            store.state('last_success',NOW)
            store.save_call('current',NOW-60,dict(port='FIHEL',mmsi='230000001',imo=None,
                previous='FIRAU',nationality=None,ata=NOW-300,atd=None))
            for spotlight in (False,True):
                data=snapshot(store,HARBORS['helsinki'],NOW,spotlight=spotlight,scale='wider')
                voyages={v['mmsi']:v.get('voyage') for v in data['vessels']}
                self.assertEqual(voyages['230000001'],'Rauma, FI → Rotterdam, NL')
                self.assertEqual(voyages['230000002'],'To Rotterdam, NL')
                self.assertNotIn('Helsinki',voyages['230000002'])
                self.assertTrue(all('facts' not in v for v in data['vessels']))
        finally:store.close()

    def test_payload_budget_drops_optional_routes_before_real_positions(self):
        vessels=[dict(mmsi=str(230000001+i),name='SHIP '+str(i),position=[24.95,60.15],voyage='港'*96) for i in range(40)]
        payload=dict(vessels=vessels,total=40,shown=40,omitted=0,focus=None)
        result=json.loads(encode_snapshot(payload))
        self.assertLess(len(encode_snapshot(result)),15000)
        self.assertEqual(len(result['vessels']),40)
        self.assertEqual(result['omitted'],0)
        self.assertTrue(any('voyage' not in v for v in result['vessels']))
        self.assertTrue(all(v['position']==[24.95,60.15] for v in result['vessels']))
