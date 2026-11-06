"""Read the free-text AIS destination field without guessing.

Crews type destinations by hand. Common shapes, all seen in live data:
UN/LOCODEs with or without a space ("GB IMM", "GBIMM"), codes followed by a
berth or anchorage ("SGSIN AEBA - P28", "US LGB 121"), from>to code pairs
("DEHAM-BEANR", "USCHSUSSAV"), port names with a state, country or terminal
suffix ("CHARLESTON SC", "ANTWERPEN HANSADOK N") and short local names
("HH", "BHV", "NYC"). This module turns those into a UN/LOCODE where the text
says so explicitly, and otherwise leaves the text alone (tidied for display).
"""
import re

# ISO 3166-1 alpha-2, so "AN TWE" in "ANTWERPEN" is never read as a code.
ISO_COUNTRIES = set('''AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO
BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG
EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID
IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA
MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA
PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST
SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE
YT ZA ZM ZW'''.split())

# Names, local spellings and common abbreviations of catalog ports, and of
# their own terminals and docks, mapped to the port's UN/LOCODE. Only names
# that identify one port are listed; ambiguous text stays as typed.
NAMES = {
    'HELSINKI': 'FIHEL', 'HELSINGFORS': 'FIHEL', 'VUOSAARI': 'FIHEL',
    'TURKU': 'FITKU', 'ABO': 'FITKU', 'ÅBO': 'FITKU',
    'RAUMA': 'FIRAU', 'RAUMO': 'FIRAU',
    'ROTTERDAM': 'NLRTM', 'EUROPOORT': 'NLRTM', 'MAASVLAKTE': 'NLRTM', 'BOTLEK': 'NLRTM', 'WAALHAVEN': 'NLRTM',
    'ANTWERP': 'BEANR', 'ANTWERPEN': 'BEANR', 'ANVERS': 'BEANR', 'DEURGANCKDOK': 'BEANR', 'ANT': 'BEANR',
    'HAMBURG': 'DEHAM', 'HH': 'DEHAM',
    'BREMERHAVEN': 'DEBRV', 'BHV': 'DEBRV',
    'FELIXSTOWE': 'GBFXT', 'HARWICH': 'GBHRW',
    'SOUTHAMPTON': 'GBSOU',
    'LOS ANGELES': 'USLAX', 'LONG BEACH': 'USLGB',
    'NEW YORK': 'USNYC', 'NYC': 'USNYC',
    'SAVANNAH': 'USSAV', 'SAV': 'USSAV',
    'HOUSTON': 'USHOU',
    'SEATTLE': 'USSEA',
    'CHARLESTON': 'USCHS',
    'SINGAPORE': 'SGSIN', 'SGP': 'SGSIN', 'SPORE': 'SGSIN',
    'LA/LB': 'USLAX', 'LALB': 'USLAX',
    'GDANSK': 'PLGDN', 'GDAŃSK': 'PLGDN', 'MERSRAGS': 'LVMRX', 'MĒRSRAGS': 'LVMRX',
}
# Trailing words that qualify a port name without changing the port.
QUALIFIERS = {'PORT', 'HARBOR', 'HARBOUR', 'ANCH', 'ANCHORAGE', 'ROADS', 'OPL', 'PILOT', 'PILOTS', 'TERMINAL',
              'CITY', 'BAR', 'SEA'}
US_STATES = set('''AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY
NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'''.split())
CATALOG = set(NAMES.values())
ARROW = re.compile(r'\s*(?:->|=>|>|\bTO\b)\s*')
CODE = r'[A-Z]{2} ?[A-Z2-9]{3}'


def _code(token):
    token = token.replace(' ', '')
    if re.fullmatch(r'[A-Z]{2}[A-Z2-9]{3}', token) and token[:2] in ISO_COUNTRIES: return token
    return None


def _pronounceable(word):
    vowels = sum(c in 'AEIOUY' for c in word)
    return vowels >= .4*len(word) and not re.search(r'[^AEIOUY]{3}', word)


def _normalize(raw):
    text = raw.upper().replace('\\', '/')
    text = re.sub(r'[.,;:]', ' ', text)
    return ' '.join(text.split())


def _tidy(words):
    """Normal case for word-like text; leave codes and run-together strings alone."""
    if len(words) > 1 and words[-1] in US_STATES: words = words[:-1]
    words = [w for w in words if w not in QUALIFIERS] or words
    def fix(w):
        # Short consonant clusters are acronyms ("APM", "ASPP"); keep them as typed.
        if not w.isalpha() or len(w) > 14 or not re.search(r'[AEIOUY]', w): return w
        if len(w) <= 4 and re.search(r'[^AEIOUY]{2}', w): return w
        return w.capitalize()
    return ' '.join(fix(w) for w in words)


def parse(raw):
    """-> dict(code=UN/LOCODE or None, text=display text if the code fails or is absent).

    Both are None for junk (placeholder or corrupted entries), so no
    destination is shown rather than noise.
    """
    if not isinstance(raw, str) or not raw.strip(): return dict(code=None, text=None)
    text = _normalize(raw)
    if re.search(r'[?^@*#$%]', text) or not re.search(r'[A-Z]{2}', text) or re.fullmatch(r'X+(?: X+)*', text):
        return dict(code=None, text=None)
    text = re.sub(r'^PORT OF ', '', text)
    # An explicit from>to: the destination is the last part.
    target = [p for p in ARROW.split(text) if p][-1]
    # Two codes as a route, run together or joined by - or /: "DEHAM-BEANR", "USCHSUSSAV".
    # Run together, a pair only counts when one end is a catalog port, so a
    # ten-letter word like "BELLINGHAM" is never split into two codes.
    m = re.fullmatch(rf'({CODE})\s*([-/]?)\s*({CODE})', target)
    if m and _code(m.group(1)) and _code(m.group(3)) and (
            m.group(2) or ' ' in target or {_code(m.group(1)), _code(m.group(3))} & CATALOG):
        return dict(code=_code(m.group(3)), text=None)
    # A known port name at the start, then only qualifiers, a state or berth detail.
    words = target.split()
    for n in range(min(3, len(words)), 0, -1):
        name = ' '.join(words[:n])
        if name in NAMES:
            rest = words[n:]
            # A short abbreviation must stand alone ("HH", not "HH 4"); names may
            # carry berth or state detail, but never an alternative port.
            if len(name) <= 3 and rest: break
            if {'OR', 'AND', '&'} & set(rest) or any(w in NAMES for w in rest if len(w) > 3): break
            return dict(code=NAMES[name], text=None)
    # A code, optionally followed by a berth or anchorage: "SGSIN AEBA - P28".
    m = re.match(rf'({CODE})(?![A-Z0-9])', target)
    if m and _code(m.group(1)):
        # A pronounceable first word ("BATAM", "CLEAN WATER") keeps its text in
        # case no such code exists; codes like "DEBRB" or "SGSIN" do not.
        word = ' ' not in m.group(1) and _pronounceable(words[0])
        return dict(code=_code(m.group(1)), text=_tidy(words) if word else None)
    return dict(code=None, text=_tidy(words))
