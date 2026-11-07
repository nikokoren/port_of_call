"""Release gates and bounded subscription planning for the reviewed registry."""
from .model import HARBORS

MESSAGE_TYPES = ['PositionReport', 'StandardClassBPositionReport',
                 'ExtendedClassBPositionReport', 'ShipStaticData', 'StaticDataReport']


def verified_harbors(provider, registry=None):
    registry = HARBORS if registry is None else registry
    return {k: h for k, h in registry.items() if h['provider']==provider and h.get('verified') is True}


# The world backend also serves the Finnish ports, fetched from the Finnish
# backend (official Digitraffic feed) over a Cloudflare service binding.
FORWARDED = {'aisstream': 'digitraffic'}


def served_harbors(provider, registry=None):
    """Harbors a backend offers: its own, then any it forwards, in catalog order."""
    own = verified_harbors(provider, registry)
    partner = FORWARDED.get(provider)
    return {**own, **(verified_harbors(partner, registry) if partner else {})}


def stream_harbors(ids=None, *, candidates=False):
    available = {k: h for k, h in HARBORS.items()
                 if h['provider']=='aisstream' and (candidates or h.get('verified') is True)}
    chosen = list(available) if ids is None else list(ids)
    if not chosen: raise ValueError('No verified AISStream harbors; run the coverage probe and review the catalog first')
    if len(chosen)>15: raise ValueError('This application limits one subscription to 15 harbor areas')
    if len(set(chosen))!=len(chosen): raise ValueError('Duplicate harbor IDs')
    if any(k not in available for k in chosen): raise ValueError('Unknown, unverified or wrong-provider harbor ID')
    return [available[k] for k in chosen]


def subscription(key, harbors):
    # API conventions differ: only the subscription uses [latitude, longitude].
    return {'APIKey':key, 'BoundingBoxes':[[[h['bbox'][1], h['bbox'][0]],
                                          [h['bbox'][3], h['bbox'][2]]] for h in harbors],
            'FilterMessageTypes':MESSAGE_TYPES.copy()}
