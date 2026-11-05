import json
import tempfile
import unittest
from unittest.mock import AsyncMock
from aiohttp import ClientConnectionError
from aiohttp.test_utils import TestClient, TestServer
from port_of_call import facts
from port_of_call.model import HARBORS, iso, position
from port_of_call.providers import aisstream, digitraffic_static
from port_of_call.store import Store
from port_of_call.spotlight import choose, card, eligible, HOLD
from port_of_call.snapshot import snapshot
from port_of_call.app import Config, create_app
from port_of_call.enrichment import Enricher, cached, save_cache, resolve_port, enrich_card, claim_values

NOW = 1793811600.0
PORT = HARBORS['helsinki']


def put(store, i=1, age=30, **fields):
    mid = str(230000000+i)
    loc = position(mid, 24.95, 60.15, NOW-age, NOW, speed=3)
    store.put(loc, dict(mmsi=mid, name='VESSEL '+str(i), type='cargo', updated_at=NOW-60,
                         facts={'call_sign': 'ABC'+str(i), 'length_m': 100+i, **fields}, facts_source='AISStream'))
    return store.vessels(NOW, 3600)[-1]


class Facts(unittest.TestCase):
    def test_unknowns_validation_and_units(self):
        self.assertEqual(facts.imo('IMO 9241061'), '9241061')
        for value in ('9241062', 0, True, None): self.assertIsNone(facts.imo(value))
        for value in ('@@@@', 'N/A', 'UNKNOWN', 'FOR ORDERS'): self.assertIsNone(facts.text(value))
        self.assertEqual(facts.dimensions(28, 172, 13, 13), (200, 26))
        for dims in [(511, 10, 63, 3), (0, 10, 0, 3), (300, 300, 60, 60)]: self.assertEqual(facts.dimensions(*dims), (None, None))
        self.assertEqual(facts.static_facts({'draught': 62}, provider='digitraffic')['draught_m'], 6.2)
        self.assertEqual(facts.static_facts({'MaximumStaticDraught': 6.2}, provider='aisstream')['draught_m'], 6.2)
        self.assertIsNone(facts.static_facts({'MaximumStaticDraught': 25.5}, provider='aisstream')['draught_m'])

    def test_eta_has_no_invented_year(self):
        self.assertEqual(facts.eta(dict(Month=12, Day=31, Hour=23, Minute=59)), '31 Dec 23:59 UTC')
        self.assertEqual(facts.packed_eta((11<<16)+(3<<11)+(17<<6)+45), '03 Nov 17:45 UTC')
        for delta in [dict(Month=0), dict(Day=0), dict(Hour=24), dict(Minute=60), dict(Month=4, Day=31)]:
            self.assertIsNone(facts.eta({**dict(Month=11, Day=3, Hour=17, Minute=45), **delta}))
        self.assertIsNotNone(facts.eta(dict(Month=2, Day=29, Hour=0, Minute=0)))

    def test_provider_facts_and_invalid_class_b_subrecord(self):
        msg = dict(MessageType='ShipStaticData', MetaData=dict(MMSI=230000001, time_utc=iso(NOW-60)),
                   Message={'ShipStaticData': dict(Name='REAL', Type=70, ImoNumber=9241061, Destination='NLRTM',
                       Dimension=dict(A=28,B=172,C=13,D=13), MaximumStaticDraught=6.2, Eta=dict(Month=12,Day=31,Hour=12,Minute=0))})
        loc, static = aisstream(msg, NOW)
        self.assertIsNone(loc); self.assertEqual(static['facts']['length_m'], 200)
        self.assertEqual(static['facts']['destination'], 'NLRTM')
        msg['MessageType']='StaticDataReport'; msg['Message']={'StaticDataReport': {'ReportA': {'Valid':False,'Name':'BAD'}, 'ReportB': {'Valid':False,'ShipType':80,'CallSign':'BAD'}}}
        _, static = aisstream(msg, NOW)
        self.assertIsNone(static['name']); self.assertEqual(static['facts'], {})

    def test_facts_expire_independently_and_out_of_order_messages(self):
        s=Store(':memory:')
        put(s, destination='NLRTM', imo='9241061')
        # A newer position/name must not suppress a valid older static fact.
        s.put(static=dict(mmsi='230000001', name='NEW', updated_at=NOW))
        s.put(static=dict(mmsi='230000001', updated_at=NOW-10, facts={'destination':'DEHAM'}))
        self.assertEqual(s.vessels(NOW,3600)[0]['facts']['destination']['value'], 'DEHAM')
        s.put(static=dict(mmsi='230000001', updated_at=NOW-20, facts={'destination':'BAD'}))
        self.assertEqual(s.vessels(NOW,3600)[0]['facts']['destination']['value'], 'DEHAM')
        s.put(static=dict(mmsi='230000001', updated_at=NOW, facts={'destination':None}))
        self.assertNotIn('destination',s.vessels(NOW,3600)[0]['facts'])
        s.put(static=dict(mmsi='230000001', updated_at=NOW, facts={'destination':'NLRTM'}))
        later=NOW+6*3600
        s.put(position('230000001',24.95,60.15,later-30,later))
        v=s.vessels(later,3600)[0]
        self.assertNotIn('destination',v['facts']);self.assertIn('imo',v['facts']);s.close()


class Selection(unittest.TestCase):
    def setUp(self):self.s=Store(':memory:');self.s.state('last_success',NOW)
    def tearDown(self):self.s.close()
    def test_shared_scale_independent_and_subject_reserved_before_limit(self):
        for i in range(1,150):put(self.s,i)
        wider=snapshot(self.s,PORT,NOW,scale='wider',spotlight=True)
        closer=snapshot(self.s,PORT,NOW+60,scale='closer',spotlight=True)
        self.assertEqual(wider['focus']['mmsi'],closer['focus']['mmsi'])
        self.assertEqual(wider['focus']['mmsi'],wider['vessels'][0]['mmsi'])
        self.assertEqual(wider['shown'],40);self.assertEqual(wider['total'],149)
        self.assertTrue(all('facts' not in v for v in wider['vessels']))
        self.assertLess(len(json.dumps(wider)),20000)
    def test_restart_hold_and_early_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d+'/s.db');put(s,1);put(s,2)
            first=choose(s,PORT,s.vessels(NOW,3600),NOW);s.close()
            s=Store(d+'/s.db');second=choose(s,PORT,s.vessels(NOW+300,3600),NOW+300)
            self.assertEqual(first[0]['mmsi'],second[0]['mmsi']);self.assertEqual(first[1],second[1])
            remaining=[v for v in s.vessels(NOW,3600) if v['mmsi']!=first[0]['mmsi']]
            self.assertNotEqual(choose(s,PORT,remaining,NOW)[0]['mmsi'],first[0]['mmsi']);s.close()
    def test_expired_unnamed_or_insufficient_candidates_fallback(self):
        put(self.s,age=901)
        self.assertIsNone(snapshot(self.s,PORT,NOW,spotlight=True)['focus'])
        self.assertEqual(snapshot(self.s,PORT,NOW,spotlight=True)['focus_mode'],'harbor')
        v=put(self.s,2);v['name']=None;self.assertFalse(eligible(v,NOW))
        v['name']='X';v['facts']={};self.assertFalse(eligible(v,NOW))
        self.s.state('last_success',NOW-2000)
        self.assertIsNone(snapshot(self.s,PORT,NOW,spotlight=True)['focus'])
    def test_rotation_avoids_recent_subject_and_history_is_bounded(self):
        for i in range(1,10):put(self.s,i)
        vs=self.s.vessels(NOW,3600);first=choose(self.s,PORT,vs,NOW)[0]['mmsi']
        later=NOW+HOLD+1
        for v in vs:v['reported_at']=iso(later-10)
        self.assertNotEqual(first,choose(self.s,PORT,vs,later)[0]['mmsi'])
        for i in range(100):self.s.db.execute('INSERT OR REPLACE INTO focus_history VALUES (?,?,?,?)',(PORT['id'],str(i),NOW+i,'cargo'))
        for v in vs:v['reported_at']=iso(later+HOLD-10)
        choose(self.s,PORT,vs,later+HOLD)
        self.assertLessEqual(self.s.db.execute('SELECT count(*) FROM focus_history').fetchone()[0],64)
    def test_selection_reason_updates_when_a_held_voyage_fact_expires(self):
        put(self.s)
        self.s.put(static=dict(mmsi='230000001',updated_at=NOW-6*3600+60,facts={'destination':'NLRTM'}))
        first=snapshot(self.s,PORT,NOW,spotlight=True)
        self.assertEqual(first['focus']['reason'],'Reported voyage details')
        second=snapshot(self.s,PORT,NOW+90,spotlight=True)
        self.assertEqual(first['focus']['mmsi'],second['focus']['mmsi'])
        self.assertIsNone(second['focus']['destination'])
        self.assertEqual(second['focus']['reason'],'Reported vessel dimensions')

    def test_missing_origin_and_truthful_reason(self):
        v=put(self.s,destination='NLRTM')
        focus=card(v,NOW,'Reported voyage details',NOW)
        self.assertIsNone(focus['origin']);self.assertEqual(focus['destination']['value'],'NLRTM')
        self.assertIn('reported_at',focus['facts'][0])


def statement(val, **extra):return dict(mainsnak=dict(snaktype='value', datavalue={'value':val}), **extra)


class Enrichment(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):self.s=Store(':memory:');self.e=Enricher(self.s,'digitraffic',clock=lambda:NOW)
    async def asyncTearDown(self):self.s.close()
    async def test_exact_imo_join_cached_and_ended_operator_excluded(self):
        entity=dict(id='Q1',claims={'P458':[statement('9241061')], 'P137':[statement({'id':'Q2'},qualifiers={'P582':[]})],
                                   'P289':[statement({'id':'Q3'})], 'P729':[statement({'time':'+2004-01-01T00:00:00Z','precision':9})]})
        self.e.request=AsyncMock(side_effect=[{'query':{'search':[{'title':'Q1'}]}},{'entities':{'Q1':entity}}, {'entities':{'Q3':{'labels':{'en':{'value':'Ocean liner'}}}}}])
        result=await self.e.refresh(None,'ship','9241061')
        self.assertEqual(result['facts'],[{'label':'Class','value':'Ocean liner'},{'label':'In service','value':'2004'}])
        await self.e.refresh(None,'ship','9241061');self.assertEqual(self.e.request.call_count,3)
        self.assertEqual(cached(self.s,'ship:9241061',NOW)[0],NOW)
    async def test_ambiguous_and_wrong_identifier_never_enrich(self):
        for entities in [{'Q1':dict(id='Q1',claims={'P458':[statement('9999999')]})},
                         {k:dict(id=k,claims={'P458':[statement('9241061')]}) for k in ['Q1','Q2']}]:
            self.e.request=AsyncMock(side_effect=[{'query':{'search':[{'title':k} for k in entities]}},{'entities':entities}])
            self.assertIsNone(await self.e.lookup(None,'P458','9241061'))
    async def test_failure_negative_cache_bounded_queue_and_daily_budget(self):
        self.e.request=AsyncMock(side_effect=ClientConnectionError('offline'))
        self.assertIsNone(await self.e.refresh(None,'ship','9241061'))
        await self.e.refresh(None,'ship','9241061');self.assertEqual(self.e.request.call_count,1)
        for i in range(1000):self.e.enqueue({'imo':str(9000000+i)})
        self.assertEqual(self.e.queue.qsize(),128)
        self.s.state('wikidata_daily_budget',json.dumps(dict(day='2026-11-04',count=500)))
        with self.assertRaisesRegex(ValueError,'budget'):await Enricher(self.s,'aisstream',clock=lambda:NOW).request(None,action='query')
    async def test_streamed_json_is_read_completely_and_budget_persists(self):
        class Content:
            async def iter_chunked(self, size):
                yield b'{"query":'
                yield b'{"search":[]}}'
        class Response:
            content=Content()
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            def raise_for_status(self):pass
        class Session:
            def get(self,*args,**kwargs):return Response()
        result=await self.e.request(Session(),action='query')
        self.assertEqual(result,{'query':{'search':[]}})
        self.assertEqual(json.loads(self.s.state('wikidata_daily_budget'))['count'],1)

    async def test_portnet_persists_only_relevant_sanitized_fields(self):
        class Response:
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            def raise_for_status(self):pass
            async def json(self):return {'portCalls':[dict(portCallId=1,portCallTimestamp=iso(NOW-60),portToVisit='FIHEL',
                 prevPort='NLRTM',imoLloyds=9241061,mmsi=230000001,shipMasterArrival='PRIVATE',agentInfo=['PRIVATE'],
                 portAreaDetails=[dict(ata=iso(NOW-300),atd=None)]),
                 dict(portCallId=2,portCallTimestamp=iso(NOW-60),portToVisit='OTHER',portAreaDetails=[])]}
        class Session:
            calls=0
            def get(self,*args,**kwargs):self.calls+=1;return Response()
        session=Session();await self.e.portnet(session);await self.e.portnet(session)
        self.assertEqual(session.calls,1)
        rows=self.s.db.execute('SELECT payload FROM port_calls').fetchall();self.assertEqual(len(rows),1)
        self.assertNotIn('PRIVATE',rows[0][0]);self.assertEqual(set(json.loads(rows[0][0])),{'port','previous','imo','mmsi','ata','atd','nationality'})

    async def test_port_exact_code_and_coordinates(self):
        entity=dict(id='Q1', labels={'en':{'value':'A real port'}}, claims={'P1937':[statement('DERSK')],
                    'P625':[statement(dict(globe='http://www.wikidata.org/entity/Q2',longitude=12,latitude=54))]})
        self.e.lookup=AsyncMock(return_value=entity)
        result=await self.e.refresh(None,'port','DERSK')
        self.assertEqual(result['position'],[12,54]);self.assertEqual(resolve_port(self.s,'DE RSK',NOW)['name'],'A real port')
        self.assertIsNone(resolve_port(self.s,'HAMBURG OR ROTTERDAM',NOW))
        self.assertEqual(resolve_port(self.s,'NLRTM',NOW)['code'],'NLRTM')
    async def test_only_relevant_actual_port_call_can_supply_origin(self):
        v=put(self.s,imo='9241061');focus=card(v,NOW,'Reported dimensions',NOW)
        base=dict(port='FIHEL',imo='9241061',mmsi=v['mmsi'],previous='NLRTM',ata=NOW-300,atd=None)
        for changes in [dict(port='FITKU'),dict(ata=NOW+300),dict(ata=None),dict(atd=NOW-100),dict(imo='9763655')]:
            self.s.db.execute('INSERT OR REPLACE INTO port_calls VALUES (?,?,?)',('test',NOW-60,json.dumps({**base,**changes})))
            enrich_card(self.s,PORT,focus,NOW);self.assertIsNone(focus['origin'])
        self.s.db.execute('INSERT OR REPLACE INTO port_calls VALUES (?,?,?)',('test',NOW-60,json.dumps(base)))
        enrich_card(self.s,PORT,focus,NOW);self.assertEqual(focus['origin']['code'],'NLRTM')


class Endpoint(unittest.IsolatedAsyncioTestCase):
    async def test_unicode_card_reserves_featured_marker_under_byte_budget(self):
        s=Store(':memory:');s.state('last_success',NOW)
        for i in range(1,100):
            put(s,i,destination='港'*48)
            s.put(static=dict(mmsi=str(230000000+i),name='船'*48,updated_at=NOW))
        async with TestClient(TestServer(create_app(Config(),store=s,collect=False,clock=lambda:NOW))) as c:
            r=await c.get('/api/v1/harbors/helsinki/vessels?spotlight=true')
            body=await r.read();data=json.loads(body)
            self.assertLess(len(body),15000);self.assertEqual(data['vessels'][0]['mmsi'],data['focus']['mmsi'])
            self.assertEqual(data['omitted'],data['total']-data['shown'])
        s.close()

    async def test_boolean_settings_budget_and_fallback(self):
        s=Store(':memory:');s.state('last_success',NOW)
        for i in range(1,100):put(s,i)
        async with TestClient(TestServer(create_app(Config(),store=s,collect=False,clock=lambda:NOW))) as c:
            for flag in ['true','on','yes','1']:
                r=await c.get('/api/v1/harbors/helsinki/vessels?spotlight='+flag);data=await r.json()
                self.assertEqual(data['focus_mode'],'ship');self.assertEqual(data['vessels'][0]['mmsi'],data['focus']['mmsi'])
                self.assertLess(len(await r.read()),15000)
            for flag in ['false','off','no','0','']:
                data=await (await c.get('/api/v1/harbors/helsinki/vessels?spotlight='+flag)).json();self.assertIsNone(data['focus'])
            self.assertEqual((await c.get('/api/v1/harbors/helsinki/vessels?spotlight=evil')).status,400)
        s.close()
