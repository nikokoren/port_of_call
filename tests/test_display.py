import unittest
from port_of_call.display import focus_copy


class Copy(unittest.TestCase):
    def base(self):
        return dict(facts=[dict(label='Type',value='Cargo vessel'),dict(label='Length / beam',value='158 × 24 m'),
                           dict(label='Speed',value='12 kn')],
                    origin=dict(value='Port of Hanko',country='Finland'),
                    destination=dict(value='GBTIL'),destination_port=dict(name='Port of Tilbury',country='United Kingdom'),
                    flag=dict(value='Netherlands',method='mmsi_mid',inferred=True),
                    eta_estimate=dict(display='10 Nov 04:00 UTC'),
                    enrichment=dict(facts=[dict(label='In service',value='2009'),dict(label='Operator',value='Company')]),
                    built_in=dict(value='Poland',label='Shipyard country'))
    def test_reported_story_and_country_labels(self):
        result=focus_copy(self.base())
        self.assertEqual(result['vessel_type'],'Cargo vessel')
        self.assertEqual(result['flag'],'Flag: Netherlands')
        self.assertEqual(result['journey']['value'],'Hanko, Finland → Tilbury, UK')
        self.assertEqual(result['eta'],'10 Nov 04:00 UTC');self.assertEqual(result['speed'],'12 knots')
    def test_missing_origin_and_country_are_omitted(self):
        f=self.base();f['origin']=None;f['destination_port']['country']=None
        result=focus_copy(f)
        self.assertEqual(result['journey'],dict(label='Destination',value='Tilbury'))
        self.assertNotIn('→',result['journey']['value'])
        f['destination']=None;self.assertIsNone(focus_copy(f)['journey'])
    def test_service_year_never_becomes_build_year(self):
        result=focus_copy(self.base())
        self.assertTrue(any(v.startswith('In service since 2009') and 'about 17 years' in v for v in result['highlights']))
        self.assertEqual(result['details'][0],dict(label='Shipyard country',value='Poland'))
        f=self.base();f['built_in']=dict(value='France',label='Built in',year=2001)
        self.assertEqual(focus_copy(f)['details'][0]['value'],'France · 2001')
    def test_dimensions_and_zero_speed_stay_meaningful(self):
        f=self.base();f['facts'][-1]['value']='0 kn'
        self.assertEqual(focus_copy(f)['speed'],'0 knots')
        self.assertEqual(focus_copy(f)['measurements'],[dict(label='Length',value='158 m'),dict(label='Width',value='24 m')])
        f['dimensions']=dict(length_m=150,beam_m=None)
        self.assertEqual(focus_copy(f)['measurements'],[dict(label='Length',value='150 m')])
    def test_no_facts_no_fabrication_and_registry_label(self):
        f=dict(facts=[])
        result=focus_copy(f)
        for key in ['vessel_type','flag','journey','eta','speed']:self.assertIsNone(result[key])
        self.assertEqual(result['measurements'],[]);self.assertEqual(result['highlights'],[])
        f['flag']=dict(value='Bermuda',method='registry_reference')
        self.assertEqual(focus_copy(f)['flag'],'Registry: Bermuda')
    def test_clean_labels_and_no_draught_in_presentation(self):
        f=self.base();f['facts'].append(dict(label='Reported draught',value='7.2 m'))
        f['flag']=dict(value='Netherlands',method='portnet_nationality')
        result=focus_copy(f)
        self.assertEqual(result['journey']['label'],'Voyage')
        self.assertEqual(result['flag'],'Flag: Netherlands')
        self.assertNotIn('draught',str(result).lower())
        self.assertNotIn('reported',str(result).lower())
    def test_long_country_names_are_shortened_on_screen(self):
        from port_of_call.model import HARBORS
        self.assertEqual(HARBORS['southampton']['country'],'UK');self.assertEqual(HARBORS['houston']['country'],'USA')
        f=self.base();f['flag']=dict(value='United States of America',method='mid_allocation')
        f['built_in']=dict(label='Shipyard country',value='United Kingdom')
        result=focus_copy(f)
        self.assertEqual(result['flag'],'Flag: USA')
        self.assertEqual(result['details'][0]['value'],'UK')
        self.assertNotIn('United',str(result))
