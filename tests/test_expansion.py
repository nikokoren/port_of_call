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
            self.assertFalse(h['verified']);self.assertTrue(contains(h['bbox'],h['center']));ZoneInfo(h['timezone'])
            w,s,e,n=h['bbox'];self.assertTrue(-180<=w<e<=180 and -90<=s<n<=90)

    def test_candidates_cannot_become_live_implicitly(self):
        self.assertEqual(set(verified_harbors('digitraffic')),{'helsinki','turku','rauma'})
        self.assertEqual(verified_harbors('aisstream'),{})
        with self.assertRaisesRegex(ValueError,'No verified'):stream_harbors()
        with self.assertRaisesRegex(ValueError,'No verified'):
            create_app(Config(provider='aisstream',key='test-only',rights=True),collect=False)

    def test_subset_validation_and_subscription_coordinate_order(self):
        hs=stream_harbors(['new-york-new-jersey','hamburg'],candidates=True)
        data=subscription('test-key',hs)
        self.assertEqual(data['BoundingBoxes'][0],[[40.49,-74.25],[40.79,-73.85]])
        self.assertIn('ShipStaticData',data['FilterMessageTypes'])
        self.assertEqual(len(subscription('test-key',stream_harbors(candidates=True))['BoundingBoxes']),15)
        for ids in (['unknown'],['helsinki'],['hamburg','hamburg'],[]):
            with self.assertRaises(ValueError):stream_harbors(ids,candidates=True)

    def test_missing_access_is_unmeasured_not_zero(self):
        e=Evidence(stream_harbors(candidates=True),NOW)
        try:
            r=e.report(NOW,'blocked',reason='Missing AISSTREAM_API_KEY')
            self.assertFalse(r['network_attempted']);self.assertFalse(r['subscription_confirmed'])
            self.assertTrue(all(h['distinct_observed'] is None for h in r['harbors']))
        finally:e.close()

    def test_reports_merging_age_fields_and_no_secrets_or_raw_positions(self):
        hs=stream_harbors(['hamburg','rotterdam'],candidates=True);e=Evidence(hs,NOW-60)
        try:
            e.observe({'MessageType':'SubscriptionConfirmation','Message':{'CompressionEnabled':True}},NOW)
            e.observe(report(hs[0]),NOW)
            e.observe(report(hs[0],when=NOW-20,TrueHeading=20),NOW)
            e.observe(report(hs[0],mid=211000002,when=NOW-2000,TrueHeading=511,Cog=360,Sog=0),NOW)
            e.observe(report(hs[0],mid=211000003,when=NOW+60),NOW)
            r=e.report(NOW,'completed',connected=True)
            h=r['harbors'][0]
            self.assertEqual(h['distinct_observed'],2);self.assertEqual(h['current_under_60min'],2)
            self.assertEqual(h['fresh_under_30min'],1);self.assertEqual(h['headings'],1)
            self.assertEqual(h['usable_orientation'],1);self.assertTrue(r['compression_confirmed'])
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
        with self.assertRaisesRegex(ValueError,'cannot be packaged'):release_settings(text,'aisstream')
        registry=copy.deepcopy(HARBORS);registry['hamburg']['verified']=True
        out=release_settings(text,'aisstream',registry=registry,origin='https://harbor.example.com')
        self.assertIn('default: hamburg',out);self.assertNotIn('default: helsinki',out)
        self.assertNotIn('Rotterdam, Netherlands',out);self.assertNotIn('Fintraffic',out)
        self.assertIn('https://harbor.example.com/api/v1/harbors/{{ harbor }}/vessels?scale={{ map_scale }}',out)
        self.assertIn("framework_version: '3.4.4'",out)
        self.assertIn('refresh_interval: 15',out)
        for origin in ('http://example.com','https://secret@example.com','https://example.com?key=secret'):
            with self.assertRaises(ValueError):release_settings(text,origin=origin)


if __name__=='__main__':unittest.main()
