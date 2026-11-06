"""Human-readable Spotlight copy; inference/provenance stays in the source fields."""
import re
from datetime import datetime, timezone


# Short forms for on-screen text; reference sources may supply the long names.
SHORT_COUNTRIES = {'United Kingdom': 'UK', 'United Kingdom of Great Britain and Northern Ireland': 'UK',
                   'United States': 'USA', 'United States of America': 'USA'}


def short_country(name):
    return SHORT_COUNTRIES.get(name, name) if isinstance(name, str) else name


def place(name, country=None):
    if not name: return None
    name = name.removeprefix('Port of ')
    country = short_country(country)
    return f'{name}, {country}' if country else name


def destination_text(raw):
    """Unresolved destination as shown: tidied text or the code, None for junk."""
    from .destinations import parse
    parsed = parse(raw)
    return parsed['text'] or parsed['code']


def destination_activity(destination):
    # This exact free-text declaration is an activity, not a named destination.
    value = (destination or {}).get('value')
    return 'Fairway works' if isinstance(value, str) and ' '.join(value.upper().split()) == 'FAIRWAY WORKS' else None


def label_voyage(context):
    """Compact route, preserving the distinction between origin and destination.

    Country codes come from resolved UN/LOCODEs, never from a ship's position.
    Raw/ambiguous destination text is retained without guessing an origin.
    """
    activity = destination_activity(context.get('destination'))
    if activity: return 'Activity: '+activity
    def location(port, name):
        code = port.get('code') or ''
        country = code[:2] if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}', code) and port.get('country') else port.get('country')
        return place(name, country)
    origin = context.get('origin') or {}
    destination = context.get('destination') or {}
    resolved = context.get('destination_port') or {}
    start = location(origin, origin.get('value'))
    end = location(resolved, resolved.get('name') or destination_text(destination.get('value'))) if destination.get('value') else None
    return start+' → '+end if start and end else 'To '+end if end else 'From '+start if start else None


def focus_copy(focus):
    facts = {f['label']: f['value'] for f in focus.get('facts', [])}
    reference = {f['label']: f['value'] for f in (focus.get('enrichment') or {}).get('facts', [])}
    origin = focus.get('origin') or {}
    destination = focus.get('destination') or {}
    resolved = focus.get('destination_port') or {}
    start = place(origin.get('value'), origin.get('country'))
    end = place(resolved.get('name') or destination_text(destination.get('value')), resolved.get('country')) if destination.get('value') else None
    journey = dict(label='Voyage', value=start+' → '+end) if start and end else (
        dict(label='Destination', value=end) if end else dict(label='Previous port', value=start) if start else None)
    activity = destination_activity(destination)
    if activity: journey = dict(label='Activity', value=activity)
    flag = focus.get('flag') or {}
    method = flag.get('method')
    flag_text = None
    if flag.get('value'):
        flag_text = ('Registry: ' if method=='registry_reference' else 'Flag: ')+short_country(flag['value'])
    highlights = []
    if reference.get('In service'): highlights.append('In service since '+reference['In service'])
    if reference.get('Operator'): highlights.append('Operator: '+reference['Operator'])
    if reference.get('Class'): highlights.append('Class: '+reference['Class'])
    details = []
    built = focus.get('built_in') or {}
    if built.get('value'):
        value = short_country(built['value'])
        # Service-entry year is not a build year. Only an explicitly supplied
        # construction year can accompany this country fact.
        year = built.get('year')
        if isinstance(year,int) and not isinstance(year,bool) and 1700<=year<=datetime.now(timezone.utc).year:
            value += f' · {year}'
        details.append(dict(label=built.get('label','Built in'),value=value))
    dimensions = focus.get('dimensions') or {}
    length, width = dimensions.get('length_m'), dimensions.get('beam_m')
    # Compatibility with historical schema-1 fixtures before dimensions were
    # retained separately. The strings came from the validated AIS adapter.
    if length is None and width is None:
        size = facts.get('Length / beam') or facts.get('Length') or ''
        match = re.fullmatch(r'(\d+(?:\.\d+)?)(?: × (\d+(?:\.\d+)?))? m',size)
        if match:
            length = float(match[1]); width = float(match[2]) if match[2] else None
    measurements = []
    if length is not None: measurements.append(dict(label='Length',value=f'{length:g} m'))
    if width is not None: measurements.append(dict(label='Width',value=f'{width:g} m'))
    return dict(vessel_type=facts.get('Type'), flag=flag_text, journey=journey,
                eta=(focus.get('eta_estimate') or {}).get('display'),
                speed=facts.get('Speed','').replace(' kn',' knots') or None,
                highlights=highlights[:2], details=details, measurements=measurements)
