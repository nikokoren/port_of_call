"""Validated reported facts. Missing fields preserve history; explicit unknowns clear it."""
import calendar
import re
from datetime import datetime, timezone
from .model import epoch, iso
from .model import name, number

VOYAGE = {'destination', 'eta', 'draught_m'}
IDENTITY_TTL = 7 * 86400
VOYAGE_TTL = 6 * 3600
NAVIGATION = {0: 'Under way using engine', 1: 'At anchor', 2: 'Not under command',
              3: 'Restricted manoeuvrability', 4: 'Constrained by draught', 5: 'Moored',
              6: 'Aground', 7: 'Fishing', 8: 'Under sail', 11: 'Towing astern', 12: 'Pushing / towing alongside'}
UNKNOWN = {'UNKNOWN', 'N/A', 'NA', 'NONE', 'NOT AVAILABLE', 'UNDEFINED', '0', '-', 'FOR ORDERS', 'ORDERS'}


def text(value):
    value = name(value) if isinstance(value, str) else None
    return None if not value or value.upper() in UNKNOWN else value


def imo(value):
    value = str(value).removeprefix('IMO').strip()
    if not re.fullmatch(r'[1-9]\d{6}', value): return None
    return value if sum(int(c) * (7-i) for i, c in enumerate(value[:6])) % 10 == int(value[6]) else None


def integer(value, low, high):
    return value if isinstance(value, int) and not isinstance(value, bool) and low <= value <= high else None


def eta(parts):
    if not isinstance(parts, dict): return None
    month, day, hour, minute = (integer(parts.get(k), *bounds) for k, bounds in
                               [('Month', (1, 12)), ('Day', (1, 31)), ('Hour', (0, 23)), ('Minute', (0, 59))])
    if None in (month, day, hour, minute) or day > calendar.monthrange(2000, month)[1]: return None
    # Preserve the yearless AIS value; a separate bounded heuristic may infer its year.
    return f'{day:02d} {calendar.month_abbr[month]} {hour:02d}:{minute:02d} UTC'


def infer_eta(fact, now):
    """Resolve only a plausible nearby year, anchored to the actual static report.

    Two days behind / 90 days ahead is an explicit heuristic, not a schedule.
    Old values are omitted rather than blindly rolled forward by a year.
    """
    if not fact: return None
    try:
        match = re.fullmatch(r'(\d{2}) ([A-Z][a-z]{2}) (\d{2}):(\d{2}) UTC', fact['value'])
        if not match: return None
        day, mon, hour, minute = match.groups()
        month = list(calendar.month_abbr).index(mon)
        reported = epoch(fact['reported_at'])
        if not 0 <= now-reported < VOYAGE_TTL: return None
        anchor = datetime.fromtimestamp(reported, timezone.utc)
        candidates = []
        for year in (anchor.year-1, anchor.year, anchor.year+1):
            try: candidate = datetime(year, month, int(day), int(hour), int(minute), tzinfo=timezone.utc)
            except ValueError: continue
            delta = candidate.timestamp()-reported
            if -2*86400 <= delta <= 90*86400 and candidate.timestamp() >= now-2*86400:
                candidates.append(candidate)
        if not candidates: return None
        result = min(candidates, key=lambda d: abs(d.timestamp()-reported))
        return dict(**fact, inferred_at=iso(result.timestamp()), year_inferred=True,
                    inference='nearest_to_report_within_minus_2_plus_90_days',
                    display=result.strftime('%d %b %H:%M UTC'))
    except (ValueError, KeyError, TypeError): return None


def radio_mid(value):
    """Only regular ship stations. Do not treat SAR, aids, groups or craft as ships."""
    value = str(value)
    return value[:3] if re.fullmatch(r'[2-7]\d{8}', value) else None


def packed_eta(value):
    if integer(value, 0, (1 << 20)-1) is None: return None
    return eta(dict(Month=(value >> 16) & 15, Day=(value >> 11) & 31,
                    Hour=(value >> 6) & 31, Minute=value & 63))


def dimensions(a, b, c, d):
    # A/B are 9-bit, C/D 6-bit. Zero is unspecified; saturated components are censored.
    def total(x, y, maximum, cap):
        if integer(x, 1, maximum-1) is None or integer(y, 1, maximum-1) is None: return None
        return x+y if x+y <= cap else None
    return total(a, b, 511, 500), total(c, d, 63, 100)


def static_facts(record, *, provider):
    result = {}
    if provider == 'digitraffic':
        mapping = {'imo': 'imo', 'callSign': 'call_sign', 'shipType': 'ship_type_code',
                   'destination': 'destination', 'eta': 'eta', 'draught': 'draught_m'}
        dims = ['referencePointA', 'referencePointB', 'referencePointC', 'referencePointD']
    else:
        mapping = {'ImoNumber': 'imo', 'CallSign': 'call_sign', 'Type': 'ship_type_code',
                   'Destination': 'destination', 'Eta': 'eta', 'MaximumStaticDraught': 'draught_m'}
        dims = ['A', 'B', 'C', 'D']
    for key, field in mapping.items():
        if key not in record: continue
        value = record[key]
        if field == 'imo': value = imo(value)
        elif field == 'ship_type_code': value = integer(value, 20, 99)
        elif field == 'eta': value = packed_eta(value) if provider == 'digitraffic' else eta(value)
        elif field == 'draught_m':
            value = number(value, 0.1, 255 if provider == 'digitraffic' else 25.5)
            value = round(value/10, 1) if value is not None and provider == 'digitraffic' else value
        else: value = text(value)
        result[field] = value
    dim_record = record if provider == 'digitraffic' else record.get('Dimension', {})
    if any(k in dim_record for k in dims):
        result['length_m'], result['beam_m'] = dimensions(*(dim_record.get(k) for k in dims))
    return result


def ship_type(code, broad=None):
    special = {20: 'Wing in ground', 30: 'Fishing vessel', 31: 'Towing vessel', 32: 'Large towing vessel',
               33: 'Dredger', 34: 'Diving operations', 35: 'Military vessel', 36: 'Sailing vessel',
               37: 'Pleasure craft', 50: 'Pilot vessel', 51: 'Search and rescue', 52: 'Tug',
               53: 'Port tender', 54: 'Anti-pollution vessel', 55: 'Law enforcement'}
    if code in special: return special[code]
    for low, label in [(40, 'High-speed craft'), (60, 'Passenger vessel'), (70, 'Cargo vessel'), (80, 'Tanker')]:
        if isinstance(code, int) and low <= code <= low+9: return label
    return (broad or 'Vessel').capitalize()
