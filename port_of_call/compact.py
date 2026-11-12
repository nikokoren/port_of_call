"""Lossless display records for the opt-in map format; legacy API stays intact."""
import copy
from .model import epoch, iso

MAP_LIMIT, CORE_LIMIT = 80, 64
MARKER_FIELDS = ['mmsi', 'position', 'bearing_deg', 'speed_knots', 'type', 'name',
                 'length_m', 'reported_at', 'stale', 'label_rank', 'voyage']


def packed(payload):
    return payload.get('schema_version') == 2 and payload.get('marker_fields') == MARKER_FIELDS


def pack(payload):
    if packed(payload): return
    rows = []
    for vessel in payload['vessels']:
        row = [vessel.get(key) for key in MARKER_FIELDS]
        row[7] = int(epoch(vessel['reported_at']))
        while row and row[-1] is None: row.pop()
        rows.append(row)
    payload.update(schema_version=2, marker_fields=MARKER_FIELDS, vessels=rows)


def unpack(payload):
    """Expand for inspection/tests, preserving original observation timestamps."""
    if not packed(payload): return copy.deepcopy(payload)
    result = copy.deepcopy(payload)
    result['vessels'] = []
    for row in payload['vessels']:
        vessel = {key: value for key,value in zip(MARKER_FIELDS,row) if value is not None}
        vessel['reported_at'] = iso(row[7])
        result['vessels'].append(vessel)
    result['schema_version'] = 1
    result.pop('marker_fields')
    return result
