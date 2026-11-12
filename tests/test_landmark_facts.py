import json
import math
from pathlib import Path
import unittest
from port_of_call.landmarks import LANDMARKS,MAX_CANDIDATES,landmarks_for
from port_of_call.port_facts import FACTS
from port_of_call.model import HARBORS
from port_of_call.memory_store import MemoryStore
from port_of_call.snapshot import snapshot
from scripts.build_landmarks import coordinate

ROOT=Path(__file__).resolve().parents[1]


class LandmarkFacts(unittest.TestCase):
    def test_every_fact_is_reviewed_and_catalog_is_in_the_correct_harbor(self):
        review=json.loads((ROOT/'docs/port-fact-poi-review.json').read_text())['facts']
        expected={f'{p}:{i}':(text,url) for p,rows in FACTS.items() for i,(text,url) in enumerate(rows)}
        self.assertEqual(len(review),len(expected))
        self.assertEqual({r['fact_id'] for r in review},set(expected))
        for row in review:self.assertEqual((row['text'],row['source_url']),expected[row['fact_id']])
        self.assertEqual(json.loads((ROOT/'docs/landmark-sources.json').read_text())['landmarks'],LANDMARKS)
        for pid,rows in LANDMARKS.items():
            self.assertEqual(len({r['source_url'] for r in rows}),len(rows))
            x,y=HARBORS[pid].get('focus') or HARBORS[pid]['center']
            for row in rows:
                lon,lat=row['position']
                self.assertLess(111*math.hypot((lon-x)*math.cos(math.radians(y)),lat-y),75,row['name'])
                for fid in row['fact_ids']:
                    self.assertIn(fid,expected);self.assertTrue(fid.startswith(pid+':'))
                    audited=next(r for r in review if r['fact_id']==fid)
                    self.assertTrue(any(p.get('reference_url')==row['source_url'] and p['decision']!='not_added' for p in audited['places']))

    def test_related_pois_always_precede_fallbacks_and_private_metadata_is_not_sent(self):
        for pid,collection in FACTS.items():
            for index in range(len(collection)):
                fid=f'{pid}:{index}'
                expected=[r['name'] for r in LANDMARKS[pid] if fid in r['fact_ids']]
                chosen=landmarks_for(pid,fid)
                self.assertEqual([r['name'] for r in chosen[:len(expected)]],expected)
                self.assertLessEqual(len(chosen),MAX_CANDIDATES)
                for row in chosen:
                    self.assertNotIn('fact_ids',row)
                    self.assertEqual(bool(row.get('fact_related')),row['name'] in expected)
                    self.assertEqual(set(row)-{'fact_related'},{'name','position','source_url'})
        self.assertEqual(landmarks_for('unsupported'),[])

    def test_snapshot_uses_actual_rotation_fact_without_changing_camera_or_vessels(self):
        store=MemoryStore();port=HARBORS['seattle']
        for index,name in [(5,'Ballard Locks'),(10,'Ballard Locks'),(6,'Space Needle'),(7,'Fishermen’s Terminal')]:
            now=3600*index
            old=snapshot(store,port,now);compact=snapshot(store,port,now,map_mode=True)
            self.assertEqual(compact['port_fact']['id'],f'seattle:{index}')
            self.assertEqual(compact['landmarks'][0]['name'],name)
            self.assertEqual(old['camera'],compact['camera']);self.assertEqual(old['vessels'],compact['vessels'])
        self.assertEqual(snapshot(store,port,5*7200,fact_period=7200)['landmarks'][0]['name'],'Ballard Locks')

    def test_coordinate_refresh_prefers_reviewed_rank_and_rejects_ambiguity(self):
        def claim(x,rank='normal'):
            return dict(rank=rank,mainsnak=dict(datavalue=dict(value=dict(longitude=x,latitude=50,globe='http://www.wikidata.org/entity/Q2'))))
        self.assertEqual(coordinate(dict(claims={'P625':[claim(1),claim(2,'preferred')]})),[2,50])
        self.assertEqual(coordinate(dict(claims={'P625':[claim(1),claim(1)]})),[1,50])
        for claims in [[],[claim(1),claim(2)],[claim(1,'deprecated')]]:
            with self.assertRaises(ValueError):coordinate(dict(claims={'P625':claims}))
