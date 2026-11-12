import copy
import json
import unittest
from aiohttp.test_utils import TestClient,TestServer
from port_of_call.app import create_app,Config
from port_of_call.compact import pack,unpack,MARKER_FIELDS
from port_of_call.model import HARBORS,position,viewport,map_candidates_view,contains
from port_of_call.memory_store import MemoryStore
from port_of_call.payload import encode_snapshot
from port_of_call.snapshot import snapshot

NOW=1794434400
PORT=HARBORS['helsinki']


def populated():
    store=MemoryStore();store.state('last_success',NOW)
    box=viewport(PORT);w,s,e,n=box
    for i in range(160):
        mid=str(230500000+i)
        store.put(position(mid,w+(i%16+.5)*(e-w)/16,s+(i//16+.5)*(n-s)/10,NOW-i,NOW,speed=4,heading=0),
            dict(mmsi=mid,name='TEST '+str(i),updated_at=NOW,type='cargo',facts=dict(length_m=100,destination='FIHEL')))
    # Synthetic unit-only observations: include one outside the core viewport.
    area=map_candidates_view(PORT,box)
    store.put(position('230599999',(w+e)/2,(area[1]+s)/2,NOW-10,NOW,speed=4),
        dict(mmsi='230599999',name='EDGE TEST',updated_at=NOW,type='passenger',facts=dict(length_m=100)))
    return store


class Compact(unittest.TestCase):
    def test_roundtrip_retains_display_fields_and_original_observation_time(self):
        s=populated();original=snapshot(s,PORT,NOW,map_mode=True)
        packed=json.loads(encode_snapshot(copy.deepcopy(original),map_mode=True))
        self.assertEqual(packed['schema_version'],2);self.assertEqual(packed['marker_fields'],MARKER_FIELDS)
        decoded=unpack(packed)
        self.assertEqual(len(decoded['vessels']),80)
        for before,after in zip(original['vessels'],decoded['vessels']):
            for key in MARKER_FIELDS:
                self.assertEqual(before.get(key),after.get(key),key)
        self.assertEqual(packed['camera'],original['camera'])
        self.assertLess(len(json.dumps(packed,separators=(',',':')).encode()),15000)

    def test_larger_pool_preserves_legacy_core_prefix_and_includes_frame_edges(self):
        s=populated();old=snapshot(s,PORT,NOW);new=snapshot(s,PORT,NOW,map_mode=True)
        self.assertEqual(len(old['vessels']),40);self.assertEqual(len(new['vessels']),80)
        self.assertEqual([v['mmsi'] for v in old['vessels']],[v['mmsi'] for v in new['vessels'][:40]])
        self.assertIn('230599999',[v['mmsi'] for v in new['vessels']])
        self.assertTrue(all(contains(new['viewport'],v['position']) for v in new['vessels']))
        self.assertEqual(old['camera'],new['camera'])

    def test_byte_budget_uses_utf8_and_keeps_featured_marker_for_long_unicode(self):
        s=populated();data=snapshot(s,PORT,NOW,map_mode=True,spotlight=True)
        for v in data['vessels']:v['name']='船'*48;v['voyage']='港'*96
        featured=data['focus']['mmsi'];body=encode_snapshot(data,map_mode=True);parsed=json.loads(body)
        self.assertLess(len(body.encode('utf-8')),15000)
        self.assertEqual(parsed['vessels'][0][0],featured)
        self.assertEqual(parsed['omitted'],parsed['total']-len(parsed['vessels']))
        self.assertEqual(encode_snapshot(parsed),body)


class CompactHTTP(unittest.IsolatedAsyncioTestCase):
    async def test_opt_in_schema_and_legacy_etags_remain_separate(self):
        store=populated()
        async with TestClient(TestServer(create_app(Config(),store=store,collect=False,clock=lambda:NOW))) as client:
            path='/api/v1/harbors/helsinki/vessels'
            old=await client.get(path);old_data=await old.json()
            new=await client.get(path+'?format=map');new_data=await new.json()
            self.assertEqual(old_data['schema_version'],1);self.assertEqual(len(old_data['vessels']),40)
            self.assertEqual(new_data['schema_version'],2);self.assertEqual(len(new_data['vessels']),80)
            self.assertNotEqual(old.headers['ETag'],new.headers['ETag'])
            self.assertEqual((await client.get(path+'?format=bogus')).status,400)
            self.assertEqual((await client.get(path+'?format=map',headers={'If-None-Match':new.headers['ETag']})).status,304)
