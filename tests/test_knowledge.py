import json
from datetime import datetime, timezone
import unittest
from port_of_call.enrichment import Enricher, save_cache
from port_of_call.memory_store import MemoryStore
from port_of_call.model import HARBORS, position
from port_of_call.spotlight import HOLD, choose, knowledge, lookups_worth_making

NOW = 1793811600.0
PORT = HARBORS['helsinki']
RECORD = dict(facts=[dict(label='Builder', value='Meyer Turku'), dict(label='Operator', value='Viking Line'),
                     dict(label='In service', value='2013')],
              built_in=dict(value='Finland'), registry_country=dict(value='Finland'))


def add(store, mid, name, facts, x=0.0, speed=4, now=NOW):
    fx, fy = PORT['focus']
    store.put(position(mid, fx+x, fy, now-30, now, speed=speed),
              dict(mmsi=mid, name=name, updated_at=now-60, type='passenger', facts=facts, facts_source='AIS'))


class Knowledge(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(); self.store.state('last_success', NOW)

    def test_a_ship_record_counts_most(self):
        facts = dict(imo='9606900', length_m=214, beam_m=31, ship_type_code=60, destination='FIHEL')
        add(self.store, '230100001', 'KNOWN', facts)
        add(self.store, '230100002', 'UNKNOWN', {**facts, 'imo': '9606901'}, x=.002)
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        save_cache(self.store, 'ship:9606901', None, NOW, 86400)  # looked up, nothing found
        ships = {v['mmsi']: v for v in self.store.vessels(NOW, 3600, PORT['bbox'])}
        known, unknown = knowledge(self.store, ships['230100001'], NOW), knowledge(self.store, ships['230100002'], NOW)
        self.assertGreater(known, unknown+40)
        # An identifier or pending lookup is not extra information on screen.
        add(self.store, '230100003', 'PENDING', {**facts, 'imo': '9606902'}, x=.004)
        add(self.store, '230100004', 'NO IMO', {k: v for k, v in facts.items() if k != 'imo'}, x=.006)
        ships = {v['mmsi']: v for v in self.store.vessels(NOW, 3600, PORT['bbox'])}
        self.assertEqual(knowledge(self.store, ships['230100003'], NOW), knowledge(self.store, ships['230100004'], NOW))

    def test_spotlight_picks_the_known_ship_most_of_the_time(self):
        picks = {'KNOWN': 0}
        for window in range(40):
            store = MemoryStore(); now = NOW+window*HOLD; store.state('last_success', now)
            base = dict(length_m=180, beam_m=28, ship_type_code=60, destination='FIHEL')
            add(store, '230200001', 'KNOWN', {**base, 'imo': '9606900'}, now=now)
            for i in range(2, 6):
                add(store, '23020000'+str(i), 'OTHER '+str(i), {**base, 'imo': '960690'+str(i)}, x=i*.002, now=now)
                save_cache(store, 'ship:960690'+str(i), None, now, 86400)
            save_cache(store, 'ship:9606900', RECORD, now, 86400)
            chosen = choose(store, PORT, store.vessels(now, 3600, PORT['bbox']), now)
            if chosen[0]['name'] == 'KNOWN': picks['KNOWN'] += 1
            self.assertEqual(chosen[2] if chosen[0]['name'] == 'KNOWN' else 'Ship record available', 'Ship record available')
        self.assertGreaterEqual(picks['KNOWN'], 24)

    def test_hidden_reference_facts_and_identifiers_do_not_inflate_information(self):
        add(self.store, '230100001', 'BUILDER ONLY', dict(imo='9606900', call_sign='ABC', length_m=100))
        add(self.store, '230100002', 'NO RECORD', dict(length_m=100), x=.002)
        save_cache(self.store, 'ship:9606900', dict(facts=[dict(label='Builder', value='Yard')]), NOW, 86400)
        vessels = self.store.vessels(NOW, 3600)
        self.assertEqual(knowledge(self.store, vessels[0], NOW), knowledge(self.store, vessels[1], NOW))

    def test_readable_destination_beats_an_unresolved_port_code(self):
        for i, dest in enumerate(['FIHEL', 'ZAQQQ']):
            add(self.store, str(230100001+i), dest, dict(destination=dest, length_m=100), x=i*.002)
        vessels = self.store.vessels(NOW, 3600)
        self.assertGreater(knowledge(self.store, vessels[0], NOW), knowledge(self.store, vessels[1], NOW))

    def test_useful_mover_beats_a_similarly_informed_large_stationary_ship(self):
        facts = dict(length_m=400, beam_m=40, ship_type_code=60, destination='FIHEL')
        add(self.store, '230100001', 'HUGE STATIONARY', facts, speed=0)
        add(self.store, '230100002', 'SMALL MOVING', {**facts, 'length_m': 90}, speed=3, x=.002)
        result = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        self.assertEqual(result[0]['name'], 'SMALL MOVING')

    def test_sparse_mover_does_not_displace_a_rich_stationary_subject(self):
        add(self.store, '230100001', 'RICH', dict(imo='9606900', length_m=200, beam_m=30,
            destination='FIHEL', ship_type_code=60), speed=0)
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        first = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        add(self.store, '230100002', 'SPARSE MOVER', dict(call_sign='ABC'), speed=4, x=.002, now=NOW+60)
        chosen = choose(self.store, PORT, self.store.vessels(NOW+60, 3600), NOW+60)
        self.assertEqual(chosen[0]['mmsi'], first[0]['mmsi'])
        self.assertEqual(chosen[1], first[1])
        # Rich information also wins a new selection, without a held subject.
        self.store.data['current'].clear(); self.store.data['history'].clear()
        self.assertEqual(choose(self.store, PORT, self.store.vessels(NOW+60, 3600), NOW+60)[0]['name'], 'RICH')

    def test_stopped_held_ship_yields_to_a_useful_mover_but_moving_hold_is_stable(self):
        facts = dict(length_m=100, beam_m=20, destination='FIHEL')
        add(self.store, '230100001', 'FIRST', facts, speed=3)
        first = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        add(self.store, '230100002', 'NEXT', facts, speed=4, x=.002, now=NOW+60)
        # Another mover arriving does not cause flicker during the normal hold.
        held = choose(self.store, PORT, self.store.vessels(NOW+60, 3600), NOW+60)
        self.assertEqual(held[1], first[1]); self.assertEqual(held[0]['name'], 'FIRST')
        add(self.store, '230100001', 'FIRST', facts, speed=0, now=NOW+120)
        changed = choose(self.store, PORT, self.store.vessels(NOW+120, 3600), NOW+120)
        self.assertEqual(changed[0]['name'], 'NEXT'); self.assertEqual(changed[1], NOW+120)

    def test_low_speed_drift_does_not_protect_a_weak_held_subject(self):
        docked = dict(length_m=14, beam_m=8, ship_type_code=37)
        add(self.store, '230100001', 'LOW SPEED AT DOCK', docked, speed=.5)
        initial = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        add(self.store, '230100002', 'FRESH UNDERWAY', dict(call_sign='ABC', ship_type_code=37),
            speed=8.4, x=.002, now=NOW+60)
        changed = choose(self.store, PORT, self.store.vessels(NOW+60, 3600), NOW+60)
        self.assertEqual(changed[0]['name'], 'FRESH UNDERWAY')
        self.assertNotEqual(changed[0]['mmsi'], initial[0]['mmsi'])

    def test_exact_priority_margin_replaces_with_an_actual_upgrade(self):
        from port_of_call.model import iso
        add(self.store, '230100001', 'LOW SPEED AT DOCK',
            dict(length_m=14, beam_m=8, ship_type_code=37), speed=.5)
        first = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        # A named, genuinely underway report with identifiers but no extra card
        # facts has exactly a 15-point priority advantage over this docked ship.
        mover = dict(mmsi='230100002', name='FRESH UNDERWAY', position=list(PORT['focus']),
            reported_at=iso(NOW+30), speed_knots=8.4, type=None,
            facts={k:dict(value=v,reported_at=iso(NOW),source='Test fixture') for k,v in
                   [('call_sign','ABC'),('imo','9000001')]})
        result = choose(self.store, PORT, [first[0], mover], NOW+60)
        self.assertEqual(result[0]['name'], 'FRESH UNDERWAY')

    def test_moving_hold_yields_when_a_much_more_informative_mover_arrives(self):
        add(self.store, '230100001', 'MOVING BASIC', dict(length_m=100), speed=4)
        first = choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)
        add(self.store, '230100002', 'MOVING RICH', dict(imo='9606900', length_m=200,
            beam_m=30, destination='FIHEL', ship_type_code=60), speed=4, x=.002, now=NOW+60)
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        changed = choose(self.store, PORT, self.store.vessels(NOW+60, 3600), NOW+60)
        self.assertNotEqual(first[0]['mmsi'], changed[0]['mmsi'])
        self.assertEqual(changed[0]['name'], 'MOVING RICH')

    def test_opaque_destination_does_not_earn_named_place_points(self):
        for i, destination in enumerate(['WSFSWUSSEAWSFSW', 'FIHEL']):
            add(self.store, str(230100001+i), destination, dict(destination=destination, length_m=100), x=i*.002)
        ships = self.store.vessels(NOW, 3600)
        self.assertLess(knowledge(self.store, ships[0], NOW), knowledge(self.store, ships[1], NOW))

    def test_slow_manoeuvring_is_not_scored_as_full_underway_motion(self):
        facts = dict(length_m=100, beam_m=20)
        add(self.store, '230100001', 'MANOEUVRING', facts, speed=1.2)
        add(self.store, '230100002', 'UNDERWAY', {**facts, 'destination':'FIHEL'}, speed=3, x=.002)
        self.assertEqual(choose(self.store, PORT, self.store.vessels(NOW, 3600), NOW)[0]['name'], 'UNDERWAY')

    def test_prefetch_prefers_a_mover_over_a_larger_stationary_ship(self):
        add(self.store, '230100001', 'BIG STOPPED', dict(imo='9606900', length_m=400), speed=0)
        add(self.store, '230100002', 'SMALL MOVING', dict(imo='9606901', length_m=80), speed=3, x=.002)
        self.assertEqual(lookups_worth_making(self.store, PORT, self.store.vessels(NOW, 3600), NOW), ['9606901', '9606900'])

    def test_lookahead_is_throttled_and_keeps_a_budget_reserve(self):
        add(self.store, '230300001', 'BIG', dict(imo='9606900', length_m=290, ship_type_code=70))
        add(self.store, '230300002', 'SMALL', dict(imo='9606901', length_m=90, ship_type_code=70), x=.002)
        vessels = self.store.vessels(NOW, 3600, PORT['bbox'])
        self.assertEqual(lookups_worth_making(self.store, PORT, vessels, NOW), ['9606900', '9606901'])
        clock = [NOW]
        enricher = Enricher(self.store, 'digitraffic', clock=lambda: clock[0])
        enricher.prefetch(PORT['id'], ['9606900']); enricher.prefetch(PORT['id'], ['9606901'])
        self.assertEqual(enricher.prefetch_queue.qsize(), 2)  # rolling shortlist, not one ship
        clock[0] += 3*3600
        self.store.state('wikidata_daily_budget', json.dumps(dict(day=datetime.fromtimestamp(clock[0], timezone.utc).strftime('%Y-%m-%d'), count=300)))
        enricher.prefetch(PORT['id'], ['9606901'])
        self.assertEqual(enricher.prefetch_queue.qsize(), 2)  # under 250 left today: Spotlight and names keep them
        save_cache(self.store, 'ship:9606900', RECORD, NOW, 86400)
        self.assertEqual(lookups_worth_making(self.store, PORT, vessels, NOW), ['9606901'])


if __name__ == '__main__':
    unittest.main()
