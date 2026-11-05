import json
import unittest
from unittest.mock import AsyncMock
from port_of_call.facts import infer_eta, radio_mid
from port_of_call.model import epoch, iso, HARBORS
from port_of_call.enrichment import Enricher, cached, save_cache, current_values, enrich_card, resolve_port
from port_of_call.store import Store

NOW = epoch('2026-11-05T08:28:29Z')


def claim(value, **extra):
    return dict(mainsnak=dict(snaktype='value',datavalue={'value':value}), **extra)


def entity(key, name, claims=None):
    return dict(id=key,labels={'en':{'value':name}},claims=claims or {})


class ETA(unittest.TestCase):
    def infer(self,value,now=NOW):
        return infer_eta(dict(value=value,reported_at=iso(now-60),source='AISStream'),now)
    def test_plausible_year_and_raw_value_preserved(self):
        result=self.infer('10 Nov 04:00 UTC')
        self.assertEqual(result['inferred_at'],'2026-11-10T04:00:00Z')
        self.assertTrue(result['year_inferred']);self.assertEqual(result['value'],'10 Nov 04:00 UTC')
    def test_december_january_rollover_and_recent_past(self):
        result=self.infer('02 Jan 04:00 UTC',epoch('2026-12-31T08:00:00Z'))
        self.assertEqual(result['inferred_at'],'2027-01-02T04:00:00Z')
        result=self.infer('31 Dec 04:00 UTC',epoch('2027-01-01T08:00:00Z'))
        self.assertEqual(result['inferred_at'],'2026-12-31T04:00:00Z')
    def test_obsolete_or_far_future_not_rolled_to_next_year(self):
        self.assertIsNone(self.infer('27 Aug 05:50 UTC'))
        self.assertIsNone(self.infer('01 Mar 08:00 UTC'))
        self.assertIsNone(self.infer('01 Nov 08:00 UTC'))
    def test_unknown_future_or_expired_report_and_calendar_validation(self):
        for value in ('unknown','31 Apr 03:00 UTC','01 Nov 25:60 UTC'):
            self.assertIsNone(self.infer(value))
        for reported in (NOW+1,NOW-6*3600):
            self.assertIsNone(infer_eta(dict(value='10 Nov 04:00 UTC',reported_at=iso(reported)),NOW))
        result=self.infer('29 Feb 04:00 UTC',epoch('2028-02-15T08:00:00Z'))
        self.assertEqual(result['inferred_at'],'2028-02-29T04:00:00Z')
        self.assertIsNone(self.infer('29 Feb 04:00 UTC',epoch('2027-02-15T08:00:00Z')))
    def test_mid_only_regular_ship_formats(self):
        self.assertEqual(radio_mid('245897000'),'245')
        for value in ('970123456','982301234','992301234','023012345','823012345','bad','23012345',None):
            self.assertIsNone(radio_mid(value))


class Countries(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.s=Store(':memory:');self.e=Enricher(self.s,'digitraffic',clock=lambda:NOW)
    async def asyncTearDown(self):self.s.close()
    async def test_mid_country_exact_reference_and_versioned_cache(self):
        self.e.lookup=AsyncMock(return_value=entity('Q55','Netherlands',{'P297':[claim('NL')]}))
        result=await self.e.refresh(None,'mid','245')
        self.assertEqual(result['name'],'Netherlands');self.e.lookup.assert_awaited_once_with(None,'P2979','245')
        self.assertEqual(cached(self.s,'country:NL',NOW)[1]['name'],'Netherlands')
        keys=[r[0] for r in self.s.db.execute('SELECT key FROM enrichment')]
        self.assertTrue(all(k.startswith('v2:') for k in keys))
    async def test_radio_region_resolves_to_country_instead_of_becoming_a_flag(self):
        self.e.lookup=AsyncMock(return_value=entity('Q26253','Madeira',{'P17':[claim({'id':'Q45'})]}))
        self.e.request=AsyncMock(return_value={'entities':{'Q45':entity('Q45','Portugal',{'P297':[claim('PT')]})}})
        result=await self.e.refresh(None,'mid','255')
        self.assertEqual(result['name'],'Portugal');self.assertEqual(result['code'],'PT')
        self.assertEqual(result['allocation_area'],'Madeira')

    async def test_real_port_country_and_ambiguous_text(self):
        self.assertEqual(resolve_port(self.s,'FIHEL',NOW)['country'],'Finland')
        self.e.lookup=AsyncMock(return_value=entity('Q1','Lisbon',{'P17':[claim({'id':'Q45'})],
            'P625':[claim(dict(globe='http://www.wikidata.org/entity/Q2',longitude=-9.1,latitude=38.7))]}))
        self.e.request=AsyncMock(return_value={'entities':{'Q45':entity('Q45','Portugal')}})
        result=await self.e.refresh(None,'port','PTLIS')
        self.assertEqual(result['country'],'Portugal')
        self.assertIsNone(resolve_port(self.s,'LISBON OR PORTO',NOW))
    async def test_builder_shipyard_country_without_headquarters_guess(self):
        ship=entity('Q1','Ship',{'P176':[claim({'id':'Q2'})]})
        self.e.lookup=AsyncMock(return_value=ship)
        for shipyard in (True,False):
            self.s.db.execute('DELETE FROM enrichment')
            builder=entity('Q2','Builder',{'P31':[claim({'id':'Q190928' if shipyard else 'Q4830453'})],
                                             'P17':[claim({'id':'Q36'})]})
            replies=[{'entities':{'Q2':builder}}]
            if shipyard:replies.append({'entities':{'Q36':entity('Q36','Poland')}})
            self.e.request=AsyncMock(side_effect=replies)
            result=await self.e.refresh(None,'ship','9345398')
            self.assertEqual(result['built_in']['value'],'Poland') if shipyard else self.assertIsNone(result['built_in'])
    async def test_explicit_creation_site_and_current_registry(self):
        ship=entity('Q1','Ship',{'P1071':[claim({'id':'Q2'})], 'P8047':[claim({'id':'Q3'},rank='preferred'),
            claim({'id':'Q4'},qualifiers={'P582':[]})]})
        self.e.lookup=AsyncMock(return_value=ship)
        self.e.request=AsyncMock(side_effect=[{'entities':{'Q2':entity('Q2','Actual yard',{'P17':[claim({'id':'Q142'})]}),
                                                          'Q3':entity('Q3','Bermuda')}},
                                             {'entities':{'Q142':entity('Q142','France')}}])
        result=await self.e.refresh(None,'ship','9241061')
        self.assertEqual(result['built_in']['label'],'Built in');self.assertEqual(result['built_in']['value'],'France')
        self.assertEqual(result['registry_country']['value'],'Bermuda')
    async def test_ended_future_and_ambiguous_registry_values(self):
        future={'P580':[{'datavalue':{'value':dict(time='+2040-01-01T00:00:00Z',precision=11)}}]}
        e=entity('Q1','Ship',{'P8047':[claim({'id':'Q2'},qualifiers=future),claim({'id':'Q3'},qualifiers={'P582':[]})]})
        self.assertEqual(current_values(e,'P8047',NOW),[])
        self.e.lookup=AsyncMock(return_value=e);self.assertIsNone(await self.e.refresh(None,'ship','9241061'))
    async def test_flag_provenance_and_relevant_reported_nationality(self):
        focus=dict(mmsi='245897000',imo='9345398',reported_at=iso(NOW-30),destination=None,enrichment=None)
        save_cache(self.s,'mid:245',dict(name='Netherlands',code='NL',url='https://www.wikidata.org/wiki/Q55'),NOW,3600)
        enrich_card(self.s,HARBORS['rauma'],focus,NOW)
        self.assertTrue(focus['flag']['inferred']);self.assertEqual(focus['flag']['label'],'Flag (AIS)')
        record=dict(port='FIRAU',imo='9345398',mmsi='245897000',ata=NOW-300,atd=None,previous='FIHEL',nationality='NL')
        self.s.db.execute('INSERT INTO port_calls VALUES (?,?,?)',('a',NOW-60,json.dumps(record)))
        enrich_card(self.s,HARBORS['rauma'],focus,NOW)
        self.assertFalse(focus['flag']['inferred']);self.assertEqual(focus['flag']['label'],'Reported flag')
        self.assertEqual(focus['origin']['country'],'Finland')
