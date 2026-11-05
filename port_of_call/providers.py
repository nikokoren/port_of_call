"""The adapters never turn static messages into position reports."""
from .model import position, name, category, epoch, mmsi
from .facts import static_facts, integer


def digitraffic(feature, now, ttl=3600):
    p = feature['properties']
    lon, lat = feature['geometry']['coordinates']
    loc = position(p['mmsi'], lon, lat, p['timestampExternal']/1000, now, ttl,
                    heading=p.get('heading'), course=p.get('cog'), speed=p.get('sog'))
    loc['navigation_status'] = integer(p.get('navStat'), 0, 14)
    return loc


def digitraffic_static(record):
    return dict(mmsi=mmsi(record.get('mmsi')), name=name(record.get('name')),
                type=category(record.get('shipType')), updated_at=epoch(record['timestamp']/1000),
                facts=static_facts(record, provider='digitraffic'), facts_source='Fintraffic / Digitraffic')


def aisstream(message, now, ttl=3600):
    kind = message.get('MessageType')
    if kind not in ('PositionReport', 'StandardClassBPositionReport', 'ExtendedClassBPositionReport',
                    'ShipStaticData', 'StaticDataReport'):
        return None, None
    meta = message['MetaData']
    data = message['Message'][kind]
    if data.get('Valid') is False: raise ValueError('Provider marked invalid')
    mid = mmsi(meta.get('MMSI'))
    if not mid: raise ValueError('Invalid MMSI')
    ts = epoch(meta.get('time_utc'))
    if not 0 <= now - ts < ttl: raise ValueError('Invalid message timestamp')
    static = dict(mmsi=mid, name=name(meta.get('ShipName')), type=None, updated_at=ts)
    if kind == 'StaticDataReport':
        a, b = data.get('ReportA', {}), data.get('ReportB', {})
        if a.get('Valid') is False: a = {}
        if b.get('Valid') is False: b = {}
        static.update(name=name(a.get('Name')) or static['name'], type=category(b.get('ShipType')))
        static['facts'] = static_facts({**b, **({'Type': b['ShipType']} if 'ShipType' in b else {})}, provider='aisstream')
    elif kind == 'ShipStaticData':
        static.update(name=name(data.get('Name')) or static['name'], type=category(data.get('Type')))
        static['facts'] = static_facts(data, provider='aisstream')
    elif kind == 'ExtendedClassBPositionReport':
        static.update(name=name(data.get('Name')) or static['name'], type=category(data.get('Type')))
        static['facts'] = static_facts(data, provider='aisstream')
    static['facts_source'] = 'AISStream'
    if kind in ('ShipStaticData', 'StaticDataReport'): return None, static
    # Never fall back to metadata coordinates: these may belong to an older report.
    loc = position(mid, data.get('Longitude'), data.get('Latitude'), ts, now, ttl,
                   heading=data.get('TrueHeading'), course=data.get('Cog'), speed=data.get('Sog'))
    loc['navigation_status'] = integer(data.get('NavigationalStatus'), 0, 14)
    return loc, static
