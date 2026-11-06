import unittest
from port_of_call.destinations import parse
from port_of_call.display import label_voyage, destination_text
from port_of_call.enrichment import resolve_port, port_key, Enricher, cached, locode_id
from port_of_call.memory_store import MemoryStore
from port_of_call.model import HARBORS, position
from port_of_call.payload import encode_snapshot
from port_of_call.snapshot import snapshot

NOW = 1793811600.0


class Parsing(unittest.TestCase):
    """Shapes seen in live AIS destination fields on 6 November 2026."""
    def test_codes_with_detail_spacing_and_routes(self):
        cases = {'GB IMM': 'GBIMM', 'GBIMM': 'GBIMM', 'JP  KRE': 'JPKRE', 'US LGB 121': 'USLGB',
                 'SGSIN AEBA - P28': 'SGSIN', 'DEHAM-BEANR': 'BEANR', 'DEHAMBEANR': 'BEANR',
                 'USCHSUSSAV': 'USSAV', 'NLRTM>DEHAM': 'DEHAM', 'HAMBURG > ROTTERDAM': 'NLRTM'}
        for raw, code in cases.items(): self.assertEqual(parse(raw)['code'], code, raw)

    def test_names_variants_and_suffixes_of_catalog_ports(self):
        cases = {'ANTWERPEN': 'BEANR', 'ANTWERPEN HANSADOK N': 'BEANR', 'ANTWERPEN  VERREBROE': 'BEANR',
                 'CHARLESTON SC': 'USCHS', 'SEATTLE WA': 'USSEA', 'SAVANNAH, GA': 'USSAV', 'SAVANNAH GA': 'USSAV',
                 'NEW YORK HARBOR': 'USNYC', 'NEW YORK, NY': 'USNYC', 'NYC': 'USNYC', 'HH': 'DEHAM', 'BHV': 'DEBRV',
                 'SGP': 'SGSIN', 'BOTLEK': 'NLRTM', 'WAALHAVEN ZUID': 'NLRTM', 'PORT OF LONG BEACH': 'USLGB',
                 'LA/LB SHIP ASSIST': 'USLAX', 'HARWICH': 'GBHRW', 'GDANSK': 'PLGDN'}
        for raw, code in cases.items(): self.assertEqual(parse(raw)['code'], code, raw)

    def test_no_guessing(self):
        # Alternatives, abbreviations with extra text and words that only look like codes.
        for raw in ('HAMBURG OR ROTTERDAM', 'HH 4', 'ANTWERPEN AND GHENT', 'USROD5USLGB', 'LTKLJBG'):
            self.assertNotIn(parse(raw)['code'], ('DEHAM', 'BEANR', 'NLRTM'), raw)
        self.assertEqual(parse('ANTWERPEN')['code'], 'BEANR')
        self.assertIsNone(parse('ANTWERPEN AND GHENT')['code'])
        # "AN TWE" is not a country code; BATAM keeps its name in case BA TAM does not exist.
        self.assertEqual(parse('BATAM'), dict(code='BATAM', text='Batam'))
        self.assertEqual(parse('CNSHA'), dict(code='CNSHA', text=None))
        for raw in ('DEBRB', 'SGSIN AEBA - P28', 'GBFAW'): self.assertIsNone(parse(raw)['text'], raw)

    def test_unknown_text_is_tidied_and_junk_dropped(self):
        self.assertEqual(parse('SCHEVENINGEN')['text'], 'Scheveningen')
        self.assertEqual(parse('KETCHIKAN AK')['text'], 'Ketchikan')
        self.assertEqual(parse('FISHING GROUNDS')['text'], 'Fishing Grounds')
        self.assertEqual(parse('WSFSWUSSEAWSFSW')['text'], 'WSFSWUSSEAWSFSW')
        self.assertEqual(parse('APM TERMINALS MAASVL')['text'], 'APM Terminals Maasvl')
        self.assertEqual(parse('AREA 51')['text'], 'Area 51')
        self.assertEqual(parse('ASPP')['text'], 'ASPP')
        self.assertEqual(parse('NY')['text'], 'NY')
        self.assertEqual(parse('I.T.C. DEER PARK')['text'], 'I T C Deer Park')
        # Seen in Hamburg: a trailing underscore and a bare qualifier.
        self.assertEqual(parse('HAMBURG_')['code'], 'DEHAM')
        self.assertEqual(parse('PORT'), dict(code=None, text=None))
        self.assertEqual(parse('ANCHORAGE')['text'], 'Anchorage')

    def test_country_prefixes_and_major_codes(self):
        self.assertEqual(parse('US SAVANNAH')['code'], 'USSAV')
        self.assertEqual(parse('SG AWPB')['code'], 'SGSIN')
        self.assertEqual(parse('USORF'), dict(code='USORF', text=None))
        self.assertEqual(parse('DE HAM'), dict(code='DEHAM', text=None))
        self.assertEqual(parse('GB HAMBURG')['code'], None)
        for raw in ('XX XXX?? ???', 'US^0XDW0YWN', 'L', '', None):
            self.assertEqual(parse(raw), dict(code=None, text=None), raw)


class Display(unittest.TestCase):
    def setUp(self): self.s = MemoryStore()

    def label(self, raw):
        context = dict(destination=dict(value=raw), destination_port=resolve_port(self.s, raw, NOW))
        return label_voyage(context)

    def test_catalog_ports_are_named_as_ports(self):
        self.assertEqual(self.label('ANTWERPEN'), 'To Antwerp, BE')
        self.assertEqual(self.label('SEATTLE WA'), 'To Seattle, US')
        self.assertEqual(self.label('HOUSTON'), 'To Houston, US')
        self.assertEqual(self.label('NEW YORK, NY'), 'To New York, US')
        self.assertEqual(self.label('SGSIN AEBA - P28'), 'To Singapore, SG')
        self.assertEqual(self.label('HARWICH'), 'To Harwich, GB')

    def test_unresolved_text_and_junk(self):
        self.assertEqual(self.label('SCHEVENINGEN'), 'To Scheveningen')
        self.assertEqual(self.label('GB FAW'), 'To GBFAW')
        self.assertIsNone(self.label('XX XXX?? ???'))
        self.assertIsNone(destination_text('US^0XDW0YWN'))

    def test_looked_up_code_is_used_for_any_spelling(self):
        self.s.save_reference('v2:port:'+locode_id('GBFAW'), dict(code='GBFAW', name='Fawley', country='UK'), NOW, 86400)
        for raw in ('GB FAW', 'GBFAW', 'GB FAW 3'): self.assertEqual(self.label(raw), 'To Fawley, GB')


class Lookups(unittest.TestCase):
    def test_every_displayed_destination_code_is_queued_once(self):
        store = MemoryStore(); store.state('last_success', NOW)
        port = HARBORS['helsinki']; x, y = port['focus']
        for i, dest in enumerate(['GB FAW', 'GBFAW', 'CNSHA', 'ANTWERPEN', 'SCHEVENINGEN']):
            mid = str(230200000+i)
            store.put(position(mid, x+i*.001, y, NOW-30, NOW, speed=2),
                      dict(mmsi=mid, name='S'+str(i), updated_at=NOW-60, facts={'destination': dest}, facts_source='AIS'))
        data = snapshot(store, port, NOW)
        self.assertEqual(data['unresolved_ports'], ['CNSHA', 'GBFAW'])
        enricher = Enricher(store, 'aisstream', clock=lambda: NOW)
        enricher.enqueue_ports(data['unresolved_ports']); enricher.enqueue_ports(['GBFAW', 'BEANR'])
        queued = [enricher.queue.get_nowait() for _ in range(enricher.queue.qsize())]
        self.assertEqual(queued, [('port', 'CN SHA'), ('port', 'GB FAW')])
        self.assertNotIn('unresolved_ports', encode_snapshot(data))
        self.assertEqual(port_key('SGSIN AEBA - P28'), 'SGSIN')


class FalseCodes(unittest.TestCase):
    def test_words_are_not_split_into_codes(self):
        self.assertIsNone(parse('BELLINGHAM')['code'])
        self.assertEqual(parse('BELLINGHAM')['text'], 'Bellingham')
        self.assertEqual(parse('CLEAN WATER')['text'], 'Clean Water')
        self.assertEqual(destination_text('CLEAN WATER'), 'Clean Water')
        for raw, code in {'DEBRVDEBRK': 'DEBRK', 'BEANRMAPTM': 'MAPTM', 'DEHAMCASJB': 'CASJB', 'NLEURGBIMM': 'GBIMM',
                          'ROTTERDAM BOTLEK BO': 'NLRTM', 'NLRTM00102CITYX1033': 'NLRTM'}.items():
            self.assertEqual(parse(raw)['code'], code, raw)
