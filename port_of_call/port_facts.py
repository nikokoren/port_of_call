"""Short, curated factual summaries; sources are retained, never fetched per user.

These describe the port/city, not live vessel activity. Four per port, reviewed
by the maintainer in the fact review page; figures were checked against the
linked source. Review again when expanding the catalog. Hourly selection is shared across installations and map modes.
"""

FACTS = {
    'helsinki': [
        ("Helsinki–Tallinn, about 80 km across, is one of Europe’s busiest passenger sea routes.", 'https://en.wikipedia.org/wiki/Helsinki%E2%80%93Tallinn_ferry'),
        ("Suomenlinna, a UNESCO-listed island fortress, guards the entrance to the South Harbour.", 'https://whc.unesco.org/en/list/583/'),
        ("Finland’s state icebreakers wait out the summer in Helsinki, at Katajanokka.", 'https://en.wikipedia.org/wiki/Katajanokka'),
        ("Vuosaari Harbour, opened in 2008, handles most of Helsinki’s container traffic.", 'https://en.wikipedia.org/wiki/Vuosaari_Harbour'),
    ],
    'turku': [
        ("Ferries from Turku thread through the Archipelago Sea and its tens of thousands of islands.", 'https://en.wikipedia.org/wiki/Archipelago_Sea'),
        ("Turku Castle, beside the harbour, dates back to around 1280.", 'https://en.wikipedia.org/wiki/Turku_Castle'),
        ("Turku was Finland’s capital until 1812, when Helsinki took over.", 'https://en.wikipedia.org/wiki/Turku'),
        ("Turku’s shipyard built Icon of the Seas, one of the largest cruise ships ever.", 'https://en.wikipedia.org/wiki/Meyer_Turku'),
    ],
    'rauma': [
        ("Old Rauma is the largest unified wooden town in the Nordic countries.", 'https://whc.unesco.org/en/list/582/'),
        ("Rauma celebrates its bobbin-lace tradition every summer during Lace Week.", 'https://en.wikipedia.org/wiki/Rauma,_Finland'),
        ("Old Rauma has been a UNESCO World Heritage site since 1991.", 'https://whc.unesco.org/en/list/582/'),
        ("Rauma handles containers, bulk cargo and roll-on/roll-off ships.", 'https://portofrauma.com/en/'),
    ],
    'rotterdam': [
        ("Rotterdam was the world’s busiest port from 1962 until 2004.", 'https://en.wikipedia.org/wiki/Port_of_Rotterdam'),
        ("Europe’s largest port stretches about 40 km from the city to the North Sea.", 'https://en.wikipedia.org/wiki/Port_of_Rotterdam'),
        ("Maasvlakte 2, opened in 2013, was built on land reclaimed from the North Sea.", 'https://en.wikipedia.org/wiki/Maasvlakte_2'),
        ("The Erasmus Bridge, nicknamed “the Swan”, spans the Nieuwe Maas in the city centre.", 'https://en.wikipedia.org/wiki/Erasmusbrug'),
    ],
    'antwerp': [
        ("Antwerp-Bruges is Europe’s second-largest port, after Rotterdam.", 'https://en.wikipedia.org/wiki/Port_of_Antwerp-Bruges'),
        ("Zaha Hadid’s Port House looks like a ship perched on top of an old fire station.", 'https://en.wikipedia.org/wiki/Port_House'),
        ("Antwerp is a world centre of the diamond trade.", 'https://en.wikipedia.org/wiki/Antwerp_diamond_district'),
        ("Antwerp and Zeebrugge merged in 2022 to form the Port of Antwerp-Bruges.", 'https://en.wikipedia.org/wiki/Port_of_Antwerp-Bruges'),
    ],
    'hamburg': [
        ("Hamburg throws its port a birthday party every May, counting from a charter of 1189.", 'https://en.wikipedia.org/wiki/Hamburg_Port_Anniversary'),
        ("The Speicherstadt, the world’s largest historic warehouse district, stands on oak piles.", 'https://whc.unesco.org/en/list/1467/'),
        ("The Elbphilharmonie concert hall was built on top of an old harbour warehouse.", 'https://en.wikipedia.org/wiki/Elbphilharmonie'),
        ("Ships sail about 110 km up the River Elbe to reach Hamburg.", 'https://en.wikipedia.org/wiki/Port_of_Hamburg'),
    ],
    'bremerhaven': [
        ("Bremerhaven imports and exports more cars than any other port in Europe.", 'https://en.wikipedia.org/wiki/Bremerhaven'),
        ("The German Emigration Center tells the stories of emigrants who sailed to America from Bremerhaven.", 'https://en.wikipedia.org/wiki/German_Emigration_Center'),
        ("Bremerhaven’s container terminal sits right where the River Weser opens into the North Sea.", 'https://en.wikipedia.org/wiki/Bremerhaven'),
        ("Bremerhaven was founded in 1827 as a deep-water port for Bremen.", 'https://en.wikipedia.org/wiki/Bremerhaven'),
    ],
    'felixstowe': [
        ("Felixstowe is Britain’s busiest container port.", 'https://en.wikipedia.org/wiki/Port_of_Felixstowe'),
        ("Felixstowe opened Britain’s first container terminal in 1967.", 'https://en.wikipedia.org/wiki/Port_of_Felixstowe'),
        ("The Mayflower’s master, Christopher Jones, came from Harwich.", 'https://en.wikipedia.org/wiki/Christopher_Jones_(captain)'),
        ("Landguard Fort has guarded the harbour mouth since the 16th century.", 'https://en.wikipedia.org/wiki/Landguard_Fort'),
    ],
    'southampton': [
        ("Titanic set sail from Southampton on 10 April 1912.", 'https://en.wikipedia.org/wiki/Titanic'),
        ("The Mayflower first set sail from Southampton in 1620, before stopping at Plymouth.", 'https://en.wikipedia.org/wiki/Mayflower'),
        ("Southampton’s double high tide gives ships an extra-long window of deep water.", 'https://en.wikipedia.org/wiki/Southampton_Water'),
        ("Southampton is the UK’s leading cruise port.", 'https://en.wikipedia.org/wiki/Port_of_Southampton'),
    ],
    'los-angeles-long-beach': [
        ("Together, Los Angeles and Long Beach are the busiest container port complex in the US.", 'https://en.wikipedia.org/wiki/San_Pedro_Bay_Port_Complex'),
        ("The retired liner Queen Mary has been moored in Long Beach since 1967.", 'https://en.wikipedia.org/wiki/RMS_Queen_Mary'),
        ("Angels Gate Lighthouse has marked the end of the LA breakwater since 1913.", 'https://en.wikipedia.org/wiki/Los_Angeles_Harbor_Light'),
        ("The Vincent Thomas Bridge, opened in 1963, links San Pedro with Terminal Island.", 'https://en.wikipedia.org/wiki/Vincent_Thomas_Bridge'),
    ],
    'new-york-new-jersey': [
        ("Container shipping began here: the Ideal X sailed from Port Newark in 1956.", 'https://en.wikipedia.org/wiki/SS_Ideal_X'),
        ("The Statue of Liberty has greeted ships in the Upper Bay since 1886.", 'https://en.wikipedia.org/wiki/Statue_of_Liberty'),
        ("About 12 million immigrants passed through Ellis Island between 1892 and 1954.", 'https://en.wikipedia.org/wiki/Ellis_Island'),
        ("The Bayonne Bridge was raised about 64 ft between 2013 and 2019 so bigger ships fit beneath.", 'https://en.wikipedia.org/wiki/Bayonne_Bridge'),
    ],
    'savannah': [
        ("Garden City is the largest single-operator container terminal in North America.", 'https://en.wikipedia.org/wiki/Port_of_Savannah'),
        ("Savannah’s terminals sit about 18 miles inland from the Atlantic, up the Savannah River.", 'https://en.wikipedia.org/wiki/Port_of_Savannah'),
        ("Old cotton warehouses line River Street on Savannah’s historic waterfront.", 'https://en.wikipedia.org/wiki/River_Street_(Savannah,_Georgia)'),
        ("A lighthouse has guided ships into the Savannah River from Tybee Island since 1736.", 'https://en.wikipedia.org/wiki/Tybee_Island_Light_Station'),
    ],
    'houston': [
        ("The Port of Houston is a 50-mile-long string of terminals along the Houston Ship Channel.", 'https://en.wikipedia.org/wiki/Port_of_Houston'),
        ("Houston is the busiest US port by foreign tonnage.", 'https://en.wikipedia.org/wiki/Port_of_Houston'),
        ("The San Jacinto Monument, where Texas won independence in 1836, overlooks the channel.", 'https://en.wikipedia.org/wiki/San_Jacinto_Monument'),
        ("Houston’s deep-water port formally opened in 1914.", 'https://en.wikipedia.org/wiki/Port_of_Houston'),
    ],
    'seattle': [
        ("Washington State Ferries, sailing from Seattle’s Colman Dock, is the largest ferry system in the US.", 'https://en.wikipedia.org/wiki/Washington_State_Ferries'),
        ("Seattle is the main home port for cruises to Alaska.", 'https://en.wikipedia.org/wiki/Port_of_Seattle'),
        ("The ports of Seattle and Tacoma joined forces as the Northwest Seaport Alliance in 2015.", 'https://en.wikipedia.org/wiki/Northwest_Seaport_Alliance'),
        ("The Port of Seattle, founded in 1911, also runs Seattle–Tacoma airport.", 'https://en.wikipedia.org/wiki/Port_of_Seattle'),
    ],
    'charleston': [
        ("Fort Sumter, at the harbor entrance, saw the first shots of the US Civil War in 1861.", 'https://en.wikipedia.org/wiki/Fort_Sumter'),
        ("At 52 ft, Charleston has the deepest harbor on the US East Coast.", 'https://en.wikipedia.org/wiki/Port_of_Charleston'),
        ("The Ravenel Bridge gives ships 186 ft of clearance on the Cooper River.", 'https://en.wikipedia.org/wiki/Arthur_Ravenel_Jr._Bridge'),
        ("Wando Welch is South Carolina Ports’ largest container terminal.", 'https://scspa.com/facilities/wando-welch-terminal/'),
    ],
    'singapore': [
        ("Modern Singapore began as a British trading port in 1819.", 'https://en.wikipedia.org/wiki/Founding_of_modern_Singapore'),
        ("Singapore is the world’s busiest transshipment port, where cargo changes ships.", 'https://en.wikipedia.org/wiki/Port_of_Singapore'),
        ("Tuas Port, opened in 2022, will be the world’s largest fully automated terminal when complete.", 'https://en.wikipedia.org/wiki/Tuas_Port'),
        ("Raffles Lighthouse has guided ships near Singapore since 1855.", 'https://en.wikipedia.org/wiki/Raffles_Lighthouse'),
    ],
}


def port_fact(port_id, now):
    collection = FACTS.get(port_id)
    if not collection: return None
    index = int(now//3600) % len(collection)
    text, source = collection[index]
    return dict(id=f'{port_id}:{index}', text=text, source_url=source)
