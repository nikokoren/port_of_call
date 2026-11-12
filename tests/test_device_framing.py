import copy
import json
from pathlib import Path
import unittest
from port_of_call.model import HARBORS,harbor_camera,harbor_view,map_candidates_view,union_view,contains,position,select_views
from port_of_call.memory_store import MemoryStore
from port_of_call.snapshot import snapshot
from port_of_call.compact import unpack
from port_of_call.payload import encode_snapshot
from port_of_call.spotlight import harbor_candidates,spotlight_areas

ROOT=Path(__file__).resolve().parents[1]
APPROVED=json.loads((ROOT/'docs/approved-framing.json').read_text())
NOW=1794480000


class DeviceFraming(unittest.TestCase):
    def test_exact_32_approved_cameras_and_unchanged_source_coverage(self):
        before=json.loads((ROOT/'docs/framing-source-baseline.json').read_text())['harbors']
        self.assertEqual(len(APPROVED['harbors']),16)
        self.assertEqual(sum(len(p) for p in APPROVED['harbors'].values()),32)
        for pid,profiles in APPROVED['harbors'].items():
            port=HARBORS[pid];self.assertEqual(port['cameras'],profiles)
            for device,c in profiles.items():
                self.assertEqual(harbor_camera(port,device),dict(center=c['focus'],zoom=c['zoom']))
                self.assertTrue(contains(harbor_view(port,device),c['focus']))
            self.assertEqual({k:v for k,v in port.items() if k not in ('focus','zoom','cameras')},
                             {k:v for k,v in before[pid].items() if k not in ('focus','zoom','cameras')})

    def test_device_queues_alternate_without_duplicates_or_camera_changes(self):
        port=copy.deepcopy(HARBORS['seattle']);cores=[harbor_view(port,d) for d in ('og','x')]
        # Synthetic unit observations: many OG-only boats must not starve X.
        west,south,east,north=cores[0]
        boats=[]
        for i in range(120):
            boats.append(position(str(230800000+i),west+(east-west)*.05,south+(north-south)*(i+.5)/120,NOW-1,NOW,speed=4))
        x,y=harbor_camera(port,'x')['center']
        for i in range(12):boats.append(position(str(230900000+i),x+i*.0001,y,NOW-1,NOW,speed=4))
        chosen=select_views(boats,cores,64,key=lambda v:0)
        self.assertEqual(len({v['mmsi'] for v in chosen}),64)
        self.assertTrue(all(str(230900000+i) in {v['mmsi'] for v in chosen} for i in range(12)))
        self.assertTrue(any(v['mmsi'].startswith('2309') for v in chosen[:4]))

    def test_compact_snapshot_covers_both_devices_and_keeps_original_fixes(self):
        for pid in APPROVED['harbors']:
            port=HARBORS[pid];store=MemoryStore();store.state('last_success',NOW)
            for i,device in enumerate(('og','x')):
                x,y=harbor_camera(port,device)['center'];mid=str(230700000+i)
                store.put(position(mid,x,y,NOW-20-i,NOW,speed=4),dict(mmsi=mid,name='UNIT '+device,updated_at=NOW,type='cargo',facts=dict(length_m=90)))
            data=snapshot(store,port,NOW,map_mode=True)
            expected=union_view([map_candidates_view(port,harbor_view(port,d),d) for d in ('og','x')])
            self.assertEqual(data['viewport'],expected)
            self.assertEqual(data['camera']['profiles'],{d:harbor_camera(port,d) for d in ('og','x')})
            legacy=snapshot(store,port,NOW)
            self.assertNotIn('profiles',legacy['camera']);self.assertEqual(legacy['viewport'],harbor_view(port))
            self.assertNotIn('cameras',data['port'])
            decoded=unpack(json.loads(encode_snapshot(copy.deepcopy(data),map_mode=True)))
            self.assertEqual(decoded['camera'],data['camera'])
            for vessel in decoded['vessels']:
                source=next(v for v in data['vessels'] if v['mmsi']==vessel['mmsi'])
                self.assertEqual(vessel['position'],source['position']);self.assertEqual(vessel['reported_at'],source['reported_at'])

    def test_spotlight_prefers_shared_visible_area_without_moving_either_camera(self):
        port=HARBORS['seattle'];x,y=harbor_camera(port,'x')['center']
        both=position('230700001',x,y,NOW-1,NOW,speed=5)
        both.update(name='UNIT MOVING',type='cargo',facts={'length_m':{'value':90}})
        core=harbor_view(port,'og');og=position('230700002',core[0]+(core[2]-core[0])*.15,core[1]+(core[3]-core[1])*.8,NOW-1,NOW,speed=5)
        og.update(name='UNIT OG ONLY',type='cargo',facts={'length_m':{'value':90}})
        self.assertTrue(all(spotlight_areas(port,harbor_view(port,d))(both) for d in ('og','x')))
        self.assertEqual(harbor_candidates(port,[both,og],NOW),[both])
