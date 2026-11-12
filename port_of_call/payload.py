"""Preserve real marker positions before optional label detail when budgeting."""
import json
from .compact import pack, packed


def encode_snapshot(payload, *, map_mode=False):
    payload.pop('unresolved_ports', None)  # internal lookup hints, never published
    if map_mode: pack(payload)
    compact = packed(payload)
    def encode(): return json.dumps(payload, ensure_ascii=not compact, separators=(',', ':'))
    def size(body): return len(body.encode('utf-8'))
    body = encode()
    # Optional map context/history yields before real vessel positions.
    if size(body) >= 15_000 and payload.pop('landmarks', None) is not None: body = encode()
    if size(body) >= 15_000 and payload.pop('port_fact', None) is not None:
        body = encode()
    for vessel in reversed(payload['vessels']):
        if size(body) < 15_000: break
        if compact:
            if len(vessel)>10: del vessel[10:];body=encode()
        elif vessel.pop('voyage', None) is not None: body = encode()
    if size(body) >= 15_000 and payload.get('focus') and payload['focus'].pop('trail', None) is not None: body = encode()
    while size(body) >= 15_000 and len(payload['vessels']) > (1 if payload.get('focus') else 0):
        payload['vessels'].pop()
        payload['shown'] = len(payload['vessels'])
        payload['omitted'] = payload['total']-payload['shown']
        body = encode()
    return body
