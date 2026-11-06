"""Short, curated factual summaries; sources are retained, never fetched per user.

These describe the port/city, not live vessel activity. Review when expanding
the catalog. Hourly selection is shared across installations and map modes.
"""

FACTS = {
    'helsinki': [
        ('Helsinki ferries connect Finland with Tallinn and Stockholm.', 'https://www.portofhelsinki.fi/en/'),
        ('Vuosaari Harbour opened in 2008.', 'https://en.wikipedia.org/wiki/Vuosaari_Harbour'),
        ('Vuosaari has a passenger terminal as well as cargo operations.', 'https://www.portofhelsinki.fi/en/'),
    ],
    'turku': [
        ('Turku ferries sail through an island-filled Baltic archipelago.', 'https://www.portofturku.fi/en/'),
        ('Turku is Finland’s oldest city.', 'https://en.wikipedia.org/wiki/Turku'),
        ('Ferries link Turku with Stockholm across the Baltic Sea.', 'https://www.portofturku.fi/en/'),
    ],
    'rauma': [
        ('Old Rauma is a UNESCO World Heritage site.', 'https://en.wikipedia.org/wiki/Old_Rauma'),
        ('Rauma handles containers, bulk cargo and roll-on/roll-off ships.', 'https://portofrauma.com/en/'),
        ('Old Rauma is known for its historic wooden buildings.', 'https://en.wikipedia.org/wiki/Old_Rauma'),
    ],
    'rotterdam': [
        ('Rotterdam grew from a small fishing village into a major port.', 'https://www.portofrotterdam.com/en/experience-online/history-port'),
        ('The Maasvlakte was built on land reclaimed from the North Sea.', 'https://en.wikipedia.org/wiki/Maasvlakte'),
    ],
    'antwerp': [
        ('Antwerp’s port spans both banks of the River Scheldt.', 'https://www.portofantwerpbruges.com/en/our-port'),
        ('Antwerp and Zeebrugge share one port authority.', 'https://www.portofantwerpbruges.com/en/our-port'),
    ],
    'hamburg': [
        ('Hamburg is a seaport on the River Elbe, inland from the North Sea.', 'https://www.hafen-hamburg.de/en/'),
        ('The Speicherstadt warehouses are a UNESCO World Heritage site.', 'https://whc.unesco.org/en/list/1467/'),
    ],
    'bremerhaven': [
        ('Bremerhaven was founded in 1827 as a port for Bremen.', 'https://en.wikipedia.org/wiki/Bremerhaven'),
        ('Bremen and Bremerhaven work together as a twin-port system.', 'https://www.bremenports.de/en/'),
    ],
    'felixstowe': [
        ('Felixstowe opened Britain’s first container terminal in 1967.', 'https://en.wikipedia.org/wiki/Port_of_Felixstowe'),
        ('Felixstowe also has roll-on/roll-off services to the Netherlands.', 'https://www.portoffelixstowe.co.uk/'),
    ],
    'southampton': [
        ('Southampton’s double tide gives ships a longer high-water window.', 'https://en.wikipedia.org/wiki/Southampton_Water'),
        ('The port handles both cruise liners and container ships.', 'https://www.abports.co.uk/locations/southampton/'),
    ],
    'los-angeles-long-beach': [
        ('The Port of Los Angeles was officially founded in 1907.', 'https://www.portoflosangeles.org/about/history'),
        ('The Panama Canal opened a new Atlantic route for Los Angeles in 1914.', 'https://www.portoflosangeles.org/about/history'),
    ],
    'new-york-new-jersey': [
        ('This harbour is shared by the states of New York and New Jersey.', 'https://en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey'),
        ('Port Newark–Elizabeth’s container terminals sit on Newark Bay.', 'https://en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey'),
    ],
    'savannah': [
        ('Savannah’s port includes Garden City and Ocean terminals.', 'https://gaports.com/facilities/port-of-savannah/'),
        ('Garden City’s on-terminal rail hub is called Mason Mega Rail.', 'https://gaports.com/facilities/port-of-savannah/'),
    ],
    'houston': [
        ('Houston’s deep-water port formally opened in 1914.', 'https://en.wikipedia.org/wiki/Port_of_Houston'),
        ('The Houston Ship Channel links inland terminals to Galveston Bay.', 'https://en.wikipedia.org/wiki/Port_of_Houston'),
    ],
    'seattle': [
        ('The Port of Seattle was established in 1911.', 'https://en.wikipedia.org/wiki/Port_of_Seattle'),
        ('Seattle’s port authority also operates Seattle–Tacoma airport.', 'https://en.wikipedia.org/wiki/Port_of_Seattle'),
    ],
    'charleston': [
        ('Wando Welch is South Carolina Ports’ largest container terminal.', 'https://scspa.com/facilities/wando-welch-terminal/'),
        ('Charleston’s Arthur Ravenel Jr. Bridge opened in 2005.', 'https://en.wikipedia.org/wiki/Arthur_Ravenel_Jr._Bridge'),
    ],
    'singapore': [
        ('Tuas Port officially opened on 1 September 2022.', 'https://www.mpa.gov.sg/maritime-singapore/port-of-the-future'),
        ('Raffles Lighthouse has guided ships near Singapore since 1855.', 'https://en.wikipedia.org/wiki/Raffles_Lighthouse'),
    ],
}


def port_fact(port_id, now):
    collection = FACTS.get(port_id)
    if not collection: return None
    index = int(now//3600) % len(collection)
    text, source = collection[index]
    return dict(id=f'{port_id}:{index}', text=text, source_url=source)
