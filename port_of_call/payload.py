"""Preserve real marker positions before optional label detail when budgeting."""
import json


def encode_snapshot(payload):
    payload.pop('unresolved_ports', None)  # internal lookup hints, never published
    def encode(): return json.dumps(payload, ensure_ascii=True, separators=(',', ':'))
    body = encode()
    if len(body) >= 15_000 and payload.pop('port_fact', None) is not None:
        body = encode()
    for vessel in reversed(payload['vessels']):
        if len(body) < 15_000: break
        if vessel.pop('voyage', None) is not None: body = encode()
    while len(body) >= 15_000 and len(payload['vessels']) > (1 if payload.get('focus') else 0):
        payload['vessels'].pop()
        payload['shown'] = len(payload['vessels'])
        payload['omitted'] = payload['total']-payload['shown']
        body = encode()
    return body
