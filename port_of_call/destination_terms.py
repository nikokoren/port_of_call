"""Reviewed exact AIS notes/routes. Never infer a ship's current voyage direction."""
import re

KITSAP = 'https://www.kitsaptransit.com/service/fast-ferry/southworth-fast-ferry'
WEST_SEATTLE = 'https://kingcounty.gov/en/dept/metro/travel-options/water-taxi/west-seattle'
WESER = 'https://www.weserfaehre.de/'
AIS = 'https://www.navcen.uscg.gov/ais-class-a-static-and-voyage-related-data'

# Sources verify the endpoints/service. The private WSFSW token itself has no
# published operator definition, so that exact expansion is inferred in metadata.
# Keep the on-screen route label concise; it never claims a current direction.
ROUTES = {
    'WSFSWUSSEAWSFSW': ('Southworth ↔ Seattle, USA', KITSAP, True),
    'USSEAWSFSWUSSEA': ('Seattle ↔ Southworth, USA', KITSAP, True),
    'P50 & WEST SEATTLE': ('Seattle Pier 50 ↔ West Seattle, USA', WEST_SEATTLE, False),
    'PIER 50 / W SEATTLE': ('Seattle Pier 50 ↔ West Seattle, USA', WEST_SEATTLE, False),
    'BREMERHAFEN-BLEXEN': ('Bremerhaven ↔ Blexen, Germany', WESER, False),
    'BREMERHAVEN-BLEXEN': ('Bremerhaven ↔ Blexen, Germany', WESER, False),
    'BREMERHAVEN-NORDENAM': ('Bremerhaven ↔ Nordenham, Germany', WESER, True),
    'BRUNSBUTTEL-HAMBURG': ('Brunsbüttel ↔ Hamburg, Germany', 'https://www.hafen-hamburg.de/en/', False),
    'HH--SALZGITTER---HH': ('Hamburg ↔ Salzgitter, Germany', 'https://www.salzgitter.de/', False),
    'KUMLINGE-ENKLINGE': ('Kumlinge ↔ Enklinge, Finland', 'https://www.alandstrafiken.ax/en', False),
    'TURKU-AIRISTO-TURKU': ('Turku ↔ Airisto, Finland', 'https://www.portofturku.fi/en/', False),
}
ACTIVITIES = {
    'LOCAL SHIFT': 'Harbor movements', 'LOCAL SHIFTS': 'Harbor movements',
    'BERTH SHIFT': 'Changing berth', 'SHIFTING': 'Harbor movements',
    'BUNKERING': 'Refueling', 'STAND BY': 'Standby', 'STANDBY': 'Standby',
    'AT ANCHOR': 'At anchor', 'ANCHORAGE': 'Anchorage',
    'FAIRWAY WORKS': 'Fairway works', 'FAIRWAY WORK': 'Fairway works',
    'ASSISTANCE': 'Assistance', 'TOWAGE': 'Towage', 'PATROL': 'Patrol',
    'HYDROGRAPHIC SURVEY': 'Hydrographic survey', 'SURVEY OPS WESER': 'Survey operations on the Weser',
    'UNDERVANNS ARBEID': 'Underwater work', 'SAR': 'Search and rescue',
    'SAR TURKU AREA': 'Search and rescue in the Turku area',
    'SEATRIAL': 'Sea trials', 'SEA TRIAL': 'Sea trials', 'SEA TRIALS': 'Sea trials', 'TRIAL': 'Trials',
    'NAV TRAINING': 'Navigation training', 'FISHING': 'Fishing', 'FISHING GROUNDS': 'Fishing grounds',
    'LOCAL': 'Local operations', 'LOCAL TOUR': 'Local tour',
    'FERRY': 'Ferry service (route unspecified)', 'SOLENT BUNKERING': 'Bunkering in the Solent',
}


def describe(raw):
    if not isinstance(raw, str): return None
    key = ' '.join(raw.upper().replace('–', '-').replace('—', '-').split())
    # Only the reviewed complete route tokens accept optional separators.
    compact = re.sub(r'[\s/\->]', '', key)
    route = ROUTES.get(key) or (ROUTES.get(compact) if compact in ('WSFSWUSSEAWSFSW', 'USSEAWSFSWUSSEA') else None)
    if route:
        text, source, inferred = route
        return dict(kind='route', label='Route', text=text,
                    source_url=source, inferred=inferred, direction_known=False)
    if key in ACTIVITIES:
        return dict(kind='activity', label='Activity', text=ACTIVITIES[key], source_url=AIS, inferred=False)
    if key == 'FOR SALE': return dict(kind='status', label='Status', text='For sale', source_url=AIS, inferred=False)
    if key == 'WSF':
        return dict(kind='note', label='Destination note', text='Washington State Ferries (route unspecified)',
                    source_url='https://wsdot.wa.gov/travel/washington-state-ferries', inferred=False)
    return None


# Explicit port entities resolve town/port duplicates in the bundled snapshot.
# Each entity has the stated P1937 code; there are no inferred coordinates.
PORT_REFERENCES = {
    'DEKEH': ('Kehl', 'Germany', 'Q15979'),
    'CAVAN': ('Vancouver', 'Canada', 'Q1187234'),
    'DECUX': ('Cuxhaven', 'Germany', 'Q4197'),
    'DESTA': ('Stade', 'Germany', 'Q6949'),
    'ESLPA': ('Las Palmas', 'Spain', 'Q3925443'),
    'USSSI': ('Brunswick, Georgia', 'USA', 'Q7231096'),
    'BEZEE': ('Zeebrugge', 'Belgium', 'Q1477819'),
    'FRLEH': ('Le Havre', 'France', 'Q1129891'),
    'FIKTK': ('Kotka', 'Finland', 'Q11872855'),
    'SESTO': ('Stockholm', 'Sweden', 'Q34966404'),
    'NLVLI': ('Vlissingen', 'Netherlands', 'Q84433203'),
    'TWKHH': ('Kaohsiung', 'Taiwan', 'Q713449'),
    'GBIPS': ('Ipswich', 'UK', 'Q85413242'),
    'USPDX': ('Portland, Oregon', 'USA', 'Q7231237'),
}
