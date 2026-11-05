import copy
import json
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo
from port_of_call.app import Config,create_app
from port_of_call.catalog import verified_harbors,stream_harbors,subscription
from port_of_call.coverage import Evidence
from port_of_call.model import HARBORS,contains,iso
from port_of_call.recipe import release_settings

NOW=1793811600.0


def report(h, mid=211000001, when=NOW-10, **fields):
    return {'MessageType':'PositionReport','MetaData':{'MMSI':mid,'ShipName':'TEST ONLY','time_utc':iso(when)},
        'Message':{'PositionReport':{'Valid':True,'Longitude':h['center'][0],'Latitude':h['center'][1],
            'TrueHeading':90,'Cog':100,'Sog':4,**fields}}}


class Expansion(unittest.TestCase):
    def test_curated_regions_bounds_and_timezones(self):
        hs=stream_harbors(candidates=True)
        self.assertEqual(len(hs),15)
        self.assertEqual({r:sum(h['region']==r for h in hs) for r in ['europe','us','asia']},
                         {'europe':6,'us':6,'asia':3})
        for h in hs:
            self.assertEqual(h['verified'],h['coverage_distinct_vessels']>0);self.assertTrue(contains(h['bbox'],h['center']));ZoneInfo(h['timezone'])
            w,s,e,n=h['bbox'];self.assertTrue(-180<=w<e<=180 and -90<=s<n<=90)

    def test_candidates_cannot_become_live_implicitly(self):
        self.assertEqual(set(verified_harbors('digitraffic')),{'helsinki','turku','rauma'})
        active=verified_harbors('aisstream')
        self.assertEqual(len(active),13)
        self.assertNotIn('shanghai-yangshan',active);self.assertNotIn('busan-new-port',active)
        self.assertEqual(len(stream_harbors()),13)
        with self.assertRaisesRegex(ValueError,'unverified'):stream_harbors(['shanghai-yangshan'])
        # Coverage success never turns on the public-display rights flag.
        with self.assertRaisesRegex(ValueError,'RIGHTS_CONFIRMED'):Config(provider='aisstream',key='test-only')

    def test_subset_validation_and_subscription_coordinate_order(self):
        hs=stream_harbors(['new-york-new-jersey','hamburg'],candidates=True)
        data=subscription('test-key',hs)
        self.assertEqual(data['BoundingBoxes'][0],[[40.49,-74.25],[40.79,-73.85]])
        self.assertIn('ShipStaticData',data['FilterMessageTypes'])
        self.assertNotIn('FiltersShipMMSI',data)
        self.assertEqual(len(subscription('test-key',stream_harbors(candidates=True))['BoundingBoxes']),15)
        for ids in (['unknown'],['helsinki'],['hamburg','hamburg'],[]):
            with self.assertRaises(ValueError):stream_harbors(ids,candidates=True)

    def test_missing_access_is_unmeasured_not_zero(self):
        e=Evidence(stream_harbors(candidates=True),NOW)
        try:
            r=e.report(NOW,'blocked',reason='Missing AISSTREAM_API_KEY')
            self.assertFalse(r['network_attempted']);self.assertFalse(r['subscription_confirmed'])
            self.assertTrue(all(h['distinct_observed'] is None for h in r['harbors']))
            self.assertTrue(all(h['spotlight_eligible'] is None and h['metadata_fields']['destination'] is None for h in r['harbors']))
        finally:e.close()

    def test_reports_merging_age_fields_and_no_secrets_or_raw_positions(self):
        hs=stream_harbors(['hamburg','rotterdam'],candidates=True);e=Evidence(hs,NOW-60)
        try:
            e.observe({'MessageType':'SubscriptionConfirmation','Message':{'CompressionEnabled':True}},NOW)
            e.observe(report(hs[0]),NOW)
            e.observe({'MessageType':'ShipStaticData','MetaData':{'MMSI':211000001,'time_utc':iso(NOW-15)},
                'Message':{'ShipStaticData':{'Valid':True,'Name':'TEST ONLY','Type':70,'Destination':'NLRTM',
                'ImoNumber':9241061,'MaximumStaticDraught':6.2,'Dimension':{'A':28,'B':172,'C':13,'D':13}}}},NOW)
            e.observe(report(hs[0],when=NOW-20,TrueHeading=20),NOW)
            e.observe(report(hs[0],mid=211000002,when=NOW-2000,TrueHeading=511,Cog=360,Sog=0),NOW)
            e.observe(report(hs[0],mid=211000003,when=NOW+60),NOW)
            r=e.report(NOW,'completed',connected=True)
            h=r['harbors'][0]
            self.assertEqual(h['distinct_observed'],2);self.assertEqual(h['current_under_60min'],2)
            self.assertEqual(h['fresh_under_30min'],1);self.assertEqual(h['headings'],1)
            self.assertEqual(h['usable_orientation'],1);self.assertTrue(r['compression_confirmed'])
            self.assertEqual(h['spotlight_eligible'],1);self.assertEqual(h['metadata_fields']['destination'],1)
            self.assertEqual(h['metadata_fields']['draught_m'],1)
            self.assertEqual(r['harbors'][1]['distinct_observed'],0)
            self.assertEqual(r['validation_rejects'],1)
            body=json.dumps(r)
            self.assertNotIn('211000001',body);self.assertNotIn('TEST ONLY',body);self.assertNotIn('APIKey',body)
            self.assertTrue(all(not x['verified'] for x in r['harbors']))
        finally:e.close()

    def test_rejected_subscription_and_bad_shapes(self):
        e=Evidence(stream_harbors(['hamburg'],candidates=True),NOW)
        try:
            e.observe(['malformed'],NOW);self.assertEqual(e.rejected,1)
            with self.assertRaises(ConnectionError):e.observe({'error':'sensitive upstream body'},NOW)
            r=e.report(NOW,'blocked',connected=True)
            self.assertIsNone(r['harbors'][0]['distinct_observed'])
        finally:e.close()

    def test_expired_reports_are_not_counted_as_current(self):
        hs=stream_harbors(['hamburg'],candidates=True);e=Evidence(hs,NOW-60)
        try:
            e.observe(report(hs[0]),NOW)
            r=e.report(NOW+3601,'completed',connected=True)
            self.assertEqual(r['harbors'][0]['distinct_observed'],1)
            self.assertEqual(r['harbors'][0]['current_under_60min'],0)
        finally:e.close()

    def test_packaging_uses_only_verified_provider_and_preserves_polling_fields(self):
        text=Path('settings.yml').read_text()
        empty=copy.deepcopy(HARBORS)
        for h in empty.values():
            if h['provider']=='aisstream':h['verified']=False
        with self.assertRaisesRegex(ValueError,'cannot be packaged'):release_settings(text,'aisstream',registry=empty)
        registry=empty;registry['hamburg']['verified']=True
        out=release_settings(text,'aisstream',registry=registry,origin='https://harbor.example.com')
        self.assertIn('default: hamburg',out);self.assertNotIn('default: helsinki',out)
        self.assertNotIn('Rotterdam, Netherlands',out);self.assertNotIn('Fintraffic',out)
        self.assertIn('https://harbor.example.com/api/v1/harbors/{{ harbor }}/vessels?scale={{ map_scale }}',out)
        self.assertIn("framework_version: '3.4.4'",out)
        self.assertIn('refresh_interval: 15',out)
        for origin in ('http://example.com','https://secret@example.com','https://example.com?key=secret'):
            with self.assertRaises(ValueError):release_settings(text,origin=origin)


class BatchedPersistence(unittest.TestCase):
    def test_stream_health_updates_are_visible_without_a_disk_commit_per_report(self):
        import sqlite3,tempfile
        from port_of_call.store import Store
        with tempfile.TemporaryDirectory() as d:
            s=Store(d+'/positions.db')
            reader=sqlite3.connect(d+'/positions.db')
            try:
                s.state('last_success',NOW,commit=False)
                self.assertEqual(s.state('last_success'),str(NOW))
                self.assertIsNone(reader.execute("SELECT value FROM state WHERE key='last_success'").fetchone())
                s.commit()
                self.assertEqual(reader.execute("SELECT value FROM state WHERE key='last_success'").fetchone()[0],str(NOW))
            finally:reader.close();s.close()

class MajorProfileEndpoints(unittest.IsolatedAsyncioTestCase):
    async def test_profile_serves_thirteen_covered_areas_and_hides_unobserved_candidates(self):
        from aiohttp.test_utils import TestClient,TestServer
        from port_of_call.model import position
        from port_of_call.store import Store
        s=Store(':memory:')
        s.put(position('211000001',9.975,53.525,NOW-60,NOW,heading=90,speed=4))
        s.state('last_success',NOW)
        config=Config(provider='aisstream',key='test-only-not-a-real-key',rights=True)
        try:
            async with TestClient(TestServer(create_app(config,store=s,collect=False,clock=lambda:NOW))) as c:
                catalog=await (await c.get('/api/v1/harbors')).json()
                self.assertEqual(len(catalog['harbors']),13)
                r=await c.get('/api/v1/harbors/hamburg/vessels')
                data=await r.json();self.assertEqual(r.status,200);self.assertEqual(data['source'],'AISStream')
                self.assertEqual(data['total'],1);self.assertIsNone(data['attribution'])
                self.assertNotIn(config.key,json.dumps(data))
                for mid in ['shanghai-yangshan','busan-new-port','helsinki']:
                    self.assertEqual((await c.get('/api/v1/harbors/'+mid+'/vessels')).status,404)
        finally:s.close()

if __name__=='__main__':unittest.main()
