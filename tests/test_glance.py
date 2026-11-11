import json
import math
import unittest
from unittest.mock import AsyncMock
from port_of_call.model import HARBORS, position
from port_of_call.memory_store import MemoryStore
from port_of_call.store import Store
from port_of_call.movement import POINTS, trail
from port_of_call.port_facts import FACTS, port_fact
from port_of_call.rotation import rotate
from port_of_call.destination_review import record_many, report
from port_of_call.enrichment import Enricher, enrich_card
from port_of_call.display import focus_copy, label_voyage
from port_of_call.landmarks import LANDMARKS
from test_spotlight import statement

NOW=1794434400


class Glance(unittest.TestCase):
    def test_real_fix_history_matches_sql_and_survives_checkpoint(self):
        sql,edge=Store(':memory:'),MemoryStore()
        try:
            for store in (sql,edge):
                for i in range(20):
                    loc=position('230100001',24.95+i*.001,60.14,NOW-2400+i*120,NOW,ttl=3600,speed=3)
                    store.put(loc)
                result=store.movement(loc,NOW)
                self.assertLessEqual(len(result),POINTS);self.assertGreater(len(result),2)
                self.assertEqual(result[-1]['position'],[round(x,5) for x in loc['position']])
                self.assertTrue(all('reported_at' in p for p in result))
            self.assertEqual(sql.movement(loc,NOW),edge.movement(loc,NOW))
            restored=MemoryStore(edge.checkpoint(NOW))
            self.assertEqual(restored.movement(loc,NOW),edge.movement(loc,NOW))
            self.assertEqual(edge.movement(loc,NOW+1801),[])
        finally:sql.close()

    def test_stopped_old_out_of_order_and_teleport_positions_do_not_form_a_trail(self):
        s=MemoryStore()
        first=position('230100001',25,60,NOW-240,NOW,speed=4);s.put(first)
        s.put(position('230100001',25.001,60,NOW-120,NOW,speed=4))
        before=s.movement(s.data['positions']['230100001'],NOW)
        s.put(position('230100001',24,59,NOW-300,NOW,speed=4))
        self.assertEqual(s.movement(s.data['positions']['230100001'],NOW),before)
        jump=position('230100001',26,61,NOW,NOW,speed=4);s.put(jump)
        self.assertEqual(s.movement(jump,NOW),[])
        self.assertEqual(trail([[NOW-1000,25,60]],jump,NOW),[])
        stopped=MemoryStore()
        for i in range(3):stopped.put(position('230100002',25+i*.001,60,NOW-240+i*120,NOW,speed=0))
        self.assertEqual(stopped.movement(stopped.data['positions']['230100002'],NOW),[])

    def test_every_fact_is_reachable_with_every_selection_length(self):
        for n in range(1,17):
            for port,collection in FACTS.items():
                seen={port_fact(port,t*900,max(3600,n*900))['id'] for t in range(0,4*n*len(collection),n)}
                self.assertEqual(len(seen),len(collection),(port,n))

    def test_review_is_bounded_deduplicated_and_does_not_publish_identifiers(self):
        s=MemoryStore();contexts=[dict(mmsi=str(230100001+i),destination=dict(value='OPAQUE123')) for i in range(3)]
        record_many(s,'seattle',contexts,NOW);record_many(s,'seattle',contexts,NOW+1)
        row=report(s,NOW)['terms'][0]
        self.assertEqual(row['vessels'],3);self.assertEqual(row['windows'],1)
        self.assertNotIn('230100001',json.dumps(report(s,NOW)))
        record_many(s,'seattle',[dict(mmsi='230100001',destination=dict(value='LOCAL SHIFTS'))],NOW)
        self.assertEqual(len(report(s,NOW)['terms']),1)
        self.assertEqual(report(s,NOW+8*86400)['terms'],[])

    def test_reviewed_activities_are_human_readable(self):
        for raw in ('LOCAL SHIFT','LOCAL SHIFTS','BERTH SHIFT','BUNKERING'):
            self.assertTrue(label_voyage(dict(destination=dict(value=raw))).startswith('Activity:'))

    def test_landmarks_are_sourced_and_cover_all_served_harbors(self):
        for port in HARBORS.values():
            if not port.get('verified'):continue
            rows=LANDMARKS[port['id']];self.assertTrue(1<=len(rows)<=2)
            for row in rows:
                self.assertTrue(row['source_url'].startswith('https://www.wikidata.org/wiki/Q'))
                self.assertTrue(all(math.isfinite(x) for x in row['position']))
                self.assertLessEqual(len(row['name']),32)


class Stories(unittest.IsolatedAsyncioTestCase):
    async def test_exact_mmsi_capacity_and_ended_names_roles_are_ranked_above_generic_facts(self):
        s=MemoryStore();e=Enricher(s,'aisstream',clock=lambda:NOW)
        ended={'P582':[{'datavalue':{'value':{'time':'+2010-01-01T00:00:00Z','precision':9}}}]}
        entity=dict(id='Q1',claims={
            'P587':[statement('230100001')], 'P1083':[statement({'amount':'+250','unit':'1'})],
            'P2561':[statement({'language':'en','text':'FORMER NAME'},qualifiers=ended)],
            'P366':[statement({'id':'Q2'},qualifiers=ended)]})
        e.lookup=AsyncMock(return_value=entity)
        e.request=AsyncMock(return_value={'entities':{'Q2':{'labels':{'en':{'value':'research vessel'}}}}})
        result=await e.refresh(None,'ship_mmsi','230100001')
        self.assertIn(dict(label='Capacity',value='250 people'),result['facts'])
        focus=dict(mmsi='230100001',reported_at='2026-11-12T00:00:00Z',facts=[],imo=None,destination=None)
        enrich_card(s,HARBORS['seattle'],focus,NOW,calls=[])
        self.assertEqual(focus_copy(focus)['highlights'],['Former role: research vessel','Former name: FORMER NAME'])
        self.assertEqual(e.lookup.call_args.args[1:3],('P587','230100001'))
        entity['claims']['P1083']=[statement({'amount':'+250','unit':'http://www.wikidata.org/entity/Q11570'})]
        e2=Enricher(MemoryStore(),'aisstream',clock=lambda:NOW);e2.lookup=AsyncMock(return_value=entity);e2.request=e.request
        result=await e2.refresh(None,'ship_mmsi','230100001')
        self.assertFalse(any(f['label']=='Capacity' for f in result['facts']))
