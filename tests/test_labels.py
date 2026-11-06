import re
import unittest
from pathlib import Path
from port_of_call.labels import interest, rank
from port_of_call.memory_store import MemoryStore
from port_of_call.model import HARBORS, position, iso, select
from port_of_call.snapshot import snapshot

NOW = 1793811600.0
PORT = dict(name='Hamburg', id='hamburg')


def ship(mmsi, name='SHIP', type=None, speed=0.0, voyage=None, age=60, length=None):
    v = dict(mmsi=mmsi, name=name, type=type, speed_knots=speed, reported_at=iso(NOW-age), position=[0, 0])
    if voyage: v['voyage'] = voyage
    if length: v['facts'] = {'length_m': {'value': length}}
    return v


def order(ships):
    rank(ships, {v['mmsi']: interest(v, NOW) for v in ships}, PORT)
    return [v['name'] for v in sorted(ships, key=lambda v: v.get('label_rank', 999))]


class Ranking(unittest.TestCase):
    def test_moving_working_ships_before_moored_pleasure_craft(self):
        names = order([ship('1', 'YACHT', 'other'), ship('2', 'BOX', 'cargo', speed=12),
                       ship('3', 'FERRY', 'passenger', speed=9), ship('4', 'OLD', 'cargo', speed=12, age=3600)])
        self.assertEqual(names[:2], ['BOX', 'FERRY'])
        self.assertEqual(names[-1], 'OLD')

    def test_departures_and_arrivals_before_ships_already_here(self):
        names = order([ship('1', 'MOORED', 'cargo', voyage='To Hamburg, DE'),
                       ship('2', 'LEAVING', 'cargo', voyage='To Rotterdam, NL'),
                       ship('3', 'ARRIVING', 'cargo', speed=6, voyage='To Hamburg, DE')])
        self.assertEqual(names, ['ARRIVING', 'LEAVING', 'MOORED'])

    def test_kinds_and_destinations_are_mixed(self):
        tankers = [ship(str(i), f'TANKER {i}', 'tanker', voyage='To Rotterdam, NL') for i in range(3)]
        names = order(tankers + [ship('9', 'TRAWLER', 'fishing', voyage='To Cuxhaven')])
        self.assertEqual(names[:2], ['TANKER 0', 'TRAWLER'])

    def test_bigger_ship_wins_a_tie_and_unnamed_ships_get_no_rank(self):
        ships = [ship('1', 'SMALL', 'cargo', length=80), ship('2', 'LARGE', 'cargo', length=300), ship('3', '3', 'cargo')]
        self.assertEqual(order(ships)[0], 'LARGE')
        self.assertNotIn('label_rank', ships[2])

    def test_select_keeps_every_area_but_sends_the_best_ship_of_a_busy_one(self):
        box = [0, 0, 8, 6]
        busy = [dict(ship(str(i), type='other'), position=[0.5, 0.5]) for i in range(5)]
        busy.append(dict(ship('9', 'BOX', 'cargo', speed=10, age=600), position=[0.5, 0.5]))
        far = dict(ship('20', 'FAR', 'other'), position=[7.5, 5.5])
        chosen = select(busy+[far], box, limit=2, key=lambda v: interest(v, NOW))
        self.assertEqual({v['name'] for v in chosen}, {'BOX', 'FAR'})


class Snapshot(unittest.TestCase):
    def test_markers_carry_a_label_rank_and_the_spotlight_ship_does_not(self):
        store = MemoryStore(); store.state('last_success', NOW)
        port = HARBORS['helsinki']; x, y = port['focus']
        for i in range(6):
            mid = str(230300000+i)
            store.put(position(mid, x+i*.002, y, NOW-30, NOW, speed=i*3),
                      dict(mmsi=mid, name=f'S{i}', updated_at=NOW-60, type='cargo' if i % 2 else 'other'))
        data = snapshot(store, port, NOW, spotlight=True)
        ranked = [v for v in data['vessels'] if 'label_rank' in v]
        self.assertEqual(sorted(v['label_rank'] for v in ranked), list(range(1, len(ranked)+1)))
        if data['focus']: self.assertNotIn('label_rank', data['vessels'][0])


class Bundle(unittest.TestCase):
    def test_cloudflare_bundle_lists_every_module_the_snapshot_imports(self):
        from scripts.prepare_cloudflare import MODULES
        package = Path(__file__).resolve().parents[1] / 'port_of_call'
        needed = {m + '.py' for f in MODULES if f.endswith('.py')
                  for m in re.findall(r'from \.(\w+) import', (package / f).read_text())}
        self.assertEqual(needed - set(MODULES), set())
