"""Human-readable Spotlight copy; inference/provenance stays in the source fields."""
import re
from datetime import datetime, timezone


def place(name, country=None):
    if not name: return None
    name = name.removeprefix('Port of ')
    return f'{name}, {country}' if country else name


def focus_copy(focus):
    facts = {f['label']: f['value'] for f in focus.get('facts', [])}
    reference = {f['label']: f['value'] for f in (focus.get('enrichment') or {}).get('facts', [])}
    origin = focus.get('origin') or {}
    destination = focus.get('destination') or {}
    resolved = focus.get('destination_port') or {}
    start = place(origin.get('value'), origin.get('country'))
    end = place(resolved.get('name') or destination.get('value'), resolved.get('country')) if destination.get('value') else None
    journey = dict(label='Voyage (reported)', value=start+' → '+end) if start and end else (
        dict(label='Reported destination', value=end) if end else dict(label='Reported previous port', value=start) if start else None)
    flag = focus.get('flag') or {}
    method = flag.get('method')
    flag_text = None
    if flag.get('value'):
        flag_text = ('Registry: ' if method=='registry_reference' else 'Flag: ')+flag['value']
        if flag.get('inferred'): flag_text += ' (AIS)'
        elif method=='portnet_nationality': flag_text += ' (reported)'
    highlights = []
    if reference.get('In service'): highlights.append('In service since '+reference['In service'])
    if reference.get('Operator'): highlights.append('Operator: '+reference['Operator'])
    if reference.get('Class'): highlights.append('Class: '+reference['Class'])
    details = []
    built = focus.get('built_in') or {}
    if built.get('value'):
        value = built['value']
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
    if facts.get('Reported draught'): details.append(dict(label='Reported draught',value=facts['Reported draught']))
    return dict(vessel_type=facts.get('Type'), flag=flag_text, journey=journey,
                eta=(focus.get('eta_estimate') or {}).get('display'),
                speed=facts.get('Speed','').replace(' kn',' knots') or None,
                highlights=highlights[:2], details=details, measurements=measurements)
