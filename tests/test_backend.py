import asyncio
import json
import tempfile
import unittest
from unittest.mock import patch
from aiohttp.test_utils import TestClient, TestServer
from port_of_call import model as m
from port_of_call.providers import aisstream, digitraffic, digitraffic_static
from port_of_call.store import Store
from port_of_call.snapshot import snapshot
from port_of_call.app import Config, create_app
from port_of_call.collector import Collector

NOW = 1793811600.0
PORT = m.HARBORS['helsinki']


def loc(mid='230941700', age=60, x=24.95, y=60.15, **kw):
    return m.position(mid,x,y,NOW-age,NOW,**kw)


def message(kind='PositionReport', **fields):
    return {'MessageType':kind,'MetaData':{'MMSI':230941700,'ShipName':'VESSEL @',
        'time_utc':m.iso(NOW-60),'Longitude':0,'Latitude':0},
        'Message':{kind:{'Longitude':24.95,'Latitude':60.15,'Valid':True,'TrueHeading':511,'Sog':3,'Cog':90,**fields}}}


class Normalization(unittest.TestCase):
    def test_dynamic_classes(self):
        for kind in ('PositionReport','StandardClassBPositionReport','ExtendedClassBPositionReport'):
            p,s=aisstream(message(kind),NOW)
            self.assertEqual(p['position'],[24.95,60.15]);self.assertEqual(s['name'],'VESSEL')
            self.assertIsNone(p['heading_deg']);self.assertEqual(m.bearing(p),90)

    def test_static_never_creates_position(self):
        for kind in ('ShipStaticData','StaticDataReport'):
            p,s=aisstream(message(kind,Name='CARGO',Type=70),NOW)
            self.assertIsNone(p);self.assertEqual(s['mmsi'],'230941700')
        p,s=aisstream(message('StaticDataReport',ReportA={'Name':'TEST'},ReportB={'ShipType':80}),NOW)
        self.assertEqual(s['type'],'tanker');self.assertEqual(s['name'],'TEST')

    def test_reject_missing_fields_and_invalid(self):
        for fields in ({'Latitude':91},{'Longitude':181},{'Latitude':None},{'Valid':False}):
            with self.assertRaises(ValueError):aisstream(message(**fields),NOW)
        msg=message();del msg['Message']['PositionReport']['Longitude']
        with self.assertRaises(ValueError):aisstream(msg,NOW)
        self.assertEqual(aisstream({'MessageType':'SubscriptionConfirmation'},NOW),(None,None))

    def test_invalid_mmsi_positions_and_timestamps(self):
        for mid in ('x','1234','000000000','1234567890',True):
            with self.assertRaises(ValueError):loc(mid=mid)
        for x,y in ((float('nan'),60),(181,60),(25,91),(True,60)):
            with self.assertRaises(ValueError):loc(x=x,y=y)
        for age in (-1,3600,5000):
            with self.assertRaises(ValueError):loc(age=age)
        for ts in ('2026-11-04T16:59:00',float('inf'),None):
            with self.assertRaises(ValueError):m.epoch(ts)

    def test_heading_course_speed_sentinels(self):
        p=loc(heading=511,course=360,speed=102.3)
        self.assertIsNone(m.bearing(p));self.assertIsNone(p['speed_knots'])
        self.assertIsNone(m.bearing(loc(course=100,speed=0)))
        self.assertEqual(m.bearing(loc(heading=0,course=100,speed=0)),0)
        self.assertEqual(m.bearing(loc(course=100,speed=1)),100)

    def test_digitraffic_real_schema(self):
        f={'geometry':{'coordinates':[24.95,60.15]},'properties':{'mmsi':230941700,
            'timestampExternal':(NOW-60)*1000,'timestamp':52,'heading':323,'cog':45.2,'sog':0}}
        p=digitraffic(f,NOW);self.assertEqual(p['reported_at'],m.iso(NOW-60))
        self.assertEqual(m.bearing(p),323)
        s=digitraffic_static({'mmsi':230941700,'timestamp':NOW*1000,'shipType':70,'name':'<bad>\x00'})
        self.assertEqual(s['type'],'cargo');self.assertEqual(s['name'],'bad')

    def test_timestamp_fraction_and_timezone(self):
        self.assertEqual(m.epoch('2026-11-04 17:00:00.000000000 +0000 UTC'),NOW)
        self.assertEqual(m.epoch('2026-11-04T19:00:00+02:00'),NOW)

    def test_bbox_coordinate_order_and_dateline(self):
        self.assertTrue(m.contains(PORT['bbox'],[24.95,60.15]))
        self.assertFalse(m.contains(PORT['bbox'],[60.15,24.95]))
        self.assertTrue(m.contains([170,-10,-170,10],[-179,0]))
        self.assertTrue(m.contains([0,0,1,1],[1,1]))
        for scale in ('closer','standard','wider','bad'):
            b=m.viewport(PORT,scale);self.assertTrue(m.contains(PORT['bbox'],b[:2]));self.assertTrue(m.contains(PORT['bbox'],b[2:]))


class Persistence(unittest.TestCase):
    def setUp(self):self.s=Store(':memory:')
    def tearDown(self):self.s.close()
    def test_upsert_order_metadata_does_not_refresh_position(self):
        self.s.put(loc(age=60));self.s.put(loc(age=120));self.s.put(static={'mmsi':'230941700','name':'NAME','type':'cargo','updated_at':NOW})
        v=self.s.vessels(NOW,3600)[0];self.assertEqual(v['reported_at'],m.iso(NOW-60));self.assertEqual(v['name'],'NAME')
        self.s.put(static={'mmsi':'230941700','name':None,'type':None,'updated_at':NOW+1})
        self.assertEqual(self.s.vessels(NOW,3600)[0]['name'],'NAME')
        self.assertEqual(self.s.vessels(NOW+3600,3600),[])
    def test_persistence_across_restart_and_prune(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d+'/s.db');s.put(loc());s.commit();s.close();s=Store(d+'/s.db')
            self.assertEqual(len(s.vessels(NOW,3600)),1)
            s.prune(NOW+3600,3600);self.assertEqual(s.vessels(NOW+3600,3600),[]);s.close()
    def test_states_and_outage(self):
        def snap(t=NOW):return snapshot(self.s,PORT,t)
        self.assertEqual(snap()['status'],'warming')
        self.s.state('last_success',NOW);self.assertEqual(snap()['status'],'empty')
        self.s.put(loc());self.assertEqual(snap()['status'],'ok')
        self.assertEqual(snap(NOW+1800)['status'],'stale')
        self.assertEqual(snap(NOW+3601)['status'],'unavailable');self.assertEqual(snap(NOW+3601)['vessels'],[])
    def test_old_vessels_and_timezone(self):
        self.s.put(loc(age=2000));self.s.state('last_success',NOW)
        data=snapshot(self.s,PORT,NOW);self.assertEqual(data['status'],'stale')
        self.assertTrue(data['vessels'][0]['stale']);self.assertEqual(data['fetched_local'],'19:00 EET')
    def test_deterministic_dense_selection_budget(self):
        vs=[loc(mid=str(230000000+i),age=60+i%50,x=24.8+(i%45)/100,y=60.06+(i%19)/100) for i in range(1000)]
        a=m.select(vs,PORT['bbox']);b=m.select(list(reversed(vs)),PORT['bbox'])
        self.assertEqual(a,b);self.assertEqual(len(a),40)
        for v in vs:self.s.put(v)
        self.s.state('last_success',NOW)
        data=snapshot(self.s,PORT,NOW,scale='wider')
        self.assertEqual(data['shown'],40);self.assertEqual(data['omitted'],960)
        self.assertLess(len(json.dumps(data)),20000)


class Endpoints(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.s=Store(':memory:');self.s.put(loc());self.s.state('last_success',NOW)
        self.client=TestClient(TestServer(create_app(Config(),store=self.s,collect=False,clock=lambda:NOW)))
        await self.client.start_server()
    async def asyncTearDown(self):await self.client.close();self.s.close()
    async def test_contract_cache_etag(self):
        r=await self.client.get('/api/v1/harbors/helsinki/vessels?scale=wider')
        self.assertEqual(r.status,200);data=await r.json();self.assertEqual(data['schema_version'],1)
        self.assertEqual(data['vessels'][0]['position'],[24.95,60.15]);self.assertFalse(data['demo'])
        self.assertIn('max-age=30',r.headers['Cache-Control']);self.assertLess(len(await r.read()),15000)
        r2=await self.client.get('/api/v1/harbors/helsinki/vessels?scale=wider',headers={'If-None-Match':r.headers['ETag']})
        self.assertEqual(r2.status,304)
    async def test_recipe_selection_endpoint_rotates(self):
        from port_of_call.rotation import ROTATION_SECONDS
        async def shown(query):
            r=await self.client.get('/api/v1/vessels'+query)
            self.assertEqual(r.status,200);return (await r.json())['port']['id']
        slot=int(NOW//ROTATION_SECONDS)
        everything=['helsinki','turku','rauma']
        self.assertEqual(await shown(''),everything[slot%3])
        self.assertEqual(await shown('?harbors='),everything[slot%3])
        self.assertEqual(await shown('?harbors=turku'),'turku')
        self.assertEqual(await shown('?harbors=rauma,turku'),['turku','rauma'][slot%2])
        # Unknown or other-provider IDs are ignored rather than breaking a device.
        self.assertEqual(await shown('?harbors=hamburg,rauma'),'rauma')
        self.assertEqual(await shown('?harbors=hamburg'),everything[slot%3])
        r=await self.client.get('/api/v1/vessels?harbors=turku&spotlight=maybe');self.assertEqual(r.status,400)
        data=await (await self.client.get('/api/v1/vessels?harbors=helsinki')).json()
        self.assertEqual(data['viewport'],m.viewport(PORT))
    def test_rotation_steps_once_per_refresh(self):
        from port_of_call.rotation import parse_selection,rotate,ROTATION_SECONDS
        active={'a':{},'b':{},'c':{}}
        self.assertEqual(parse_selection(' c , a,a ',active),['a','c'])
        self.assertEqual(parse_selection('',active),['a','b','c'])
        seen=[rotate(['a','b','c'],ROTATION_SECONDS*k+5) for k in range(6)]
        self.assertEqual(seen,['a','b','c','a','b','c'])
        self.assertEqual({rotate(['b'],t) for t in range(0,10*ROTATION_SECONDS,600)},{'b'})
    async def test_bad_inputs_demo_off(self):
        for url,status in [('/api/v1/harbors/bad/vessels',404),('/api/v1/harbors/hamburg/vessels',404),
                           ('/api/v1/harbors/helsinki/vessels?scale=evil',400),('/demo/api/v1/harbors/helsinki/vessels',404)]:
            self.assertEqual((await self.client.get(url)).status,status)
    async def test_readiness_catalog_and_rate(self):
        self.assertEqual((await self.client.get('/health')).status,200)
        data=await (await self.client.get('/api/v1/harbors')).json()
        self.assertEqual(len(data['harbors']),3)
        for i in range(121):r=await self.client.get('/api/v1/harbors/helsinki/vessels')
        self.assertEqual(r.status,429);self.assertEqual(r.headers['Retry-After'],'60')
    async def test_degraded_after_restart_without_data(self):
        self.s.db.execute('DELETE FROM state');self.s.db.commit()
        self.assertEqual((await self.client.get('/health')).status,503)


class Configuration(unittest.TestCase):
    def test_guardrails(self):
        for kwargs in ({'fresh':4000},{'poll_seconds':5},{'provider':'bogus'},{'provider':'aisstream','key':'test'}):
            with self.assertRaises(ValueError):Config(**kwargs)


class MoreEndpoints(unittest.IsolatedAsyncioTestCase):
    async def test_demo_is_opt_in_labelled_and_isolated(self):
        s=Store(':memory:')
        async with TestClient(TestServer(create_app(Config(demo=True),store=s,collect=False,clock=lambda:NOW))) as c:
            r=await c.get('/demo/api/v1/harbors/helsinki/vessels')
            data=await r.json();self.assertTrue(data['demo']);self.assertIn('DEMO',data['source'])
            self.assertGreater(len(data['vessels']),0)
            data=await (await c.get('/api/v1/harbors/helsinki/vessels')).json()
            self.assertFalse(data['demo']);self.assertEqual(data['vessels'],[])
        s.close()

    async def test_unicode_worst_case_byte_budget(self):
        s=Store(':memory:')
        for i in range(100):
            mid=str(230000001+i)
            s.put(loc(mid=mid),{'mmsi':mid,'name':'船'*48,'type':'cargo','updated_at':NOW})
        s.state('last_success',NOW)
        async with TestClient(TestServer(create_app(Config(),store=s,collect=False,clock=lambda:NOW))) as c:
            r=await c.get('/api/v1/harbors/helsinki/vessels');body=await r.read();data=json.loads(body)
            self.assertEqual(r.status,200);self.assertLess(len(body),15000)
            self.assertEqual(data['omitted'],100-data['shown'])
        s.close()

class CollectorChecks(unittest.TestCase):
    def test_outside_area_not_retained(self):
        s=Store(':memory:');c=Collector(s,Config())
        c.ingest(loc(x=0,y=0));self.assertEqual(s.vessels(NOW,3600),[])
        c.ingest(loc());self.assertEqual(len(s.vessels(NOW,3600)),1);s.close()

    def test_cross_provider_database_cannot_mix_attribution(self):
        s=Store(':memory:');s.state('provider','aisstream')
        with self.assertRaisesRegex(ValueError,'separate DB_PATH'):create_app(Config(),store=s,collect=False)
        s.close()

class PollingChecks(unittest.IsolatedAsyncioTestCase):
    async def test_static_outage_does_not_block_real_positions(self):
        import aiohttp
        class Response:
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            def raise_for_status(self):pass
            async def json(self):return {'features':[{'geometry':{'coordinates':[24.95,60.15]},
                'properties':{'mmsi':230941700,'timestampExternal':(NOW-60)*1000}}]}
        class Session:
            def get(self,url,headers):
                assert headers['Accept-Encoding']=='gzip'
                if url.endswith('/vessels'):raise aiohttp.ClientConnectionError('test metadata outage')
                return Response()
        s=Store(':memory:');c=Collector(s,Config())
        with patch('port_of_call.collector.time.time',return_value=NOW):await c.poll(Session())
        self.assertEqual(len(s.vessels(NOW,3600)),1)
        self.assertEqual(s.state('last_success'),str(NOW));self.assertTrue(c.connected)
        self.assertIsNone(s.vessels(NOW,3600)[0]['name']);s.close()

if __name__=='__main__':unittest.main()
