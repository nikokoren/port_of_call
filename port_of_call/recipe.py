"""Build a polling form from verified provider coverage, never from candidates."""
import json
import re
from urllib.parse import urlsplit
from .catalog import verified_harbors


def release_settings(text, provider='digitraffic', *, origin=None, registry=None):
    harbors=list(verified_harbors(provider,registry).values())
    if not harbors: raise ValueError('No verified harbors for '+provider+'; candidate ports cannot be packaged')
    # Keep the hand-written field header (name, help text, multiple/optional)
    # and replace only its options with the verified catalog.
    options='    options:\n'+''.join('      - '+json.dumps(h['name']+', '+h['country'],ensure_ascii=False)+': '+json.dumps(h['id'])+'\n'
                                  for h in harbors)
    text,n=re.subn(r'(  - keyname: harbor\n(?:(?!  - keyname:|    options:\n).*\n)*)    options:\n(?:      - .*\n)*(?:    default: .*\n)?',
                   lambda m:m.group(1)+options,text,count=1)
    if n!=1: raise ValueError('Harbor form field not found')
    if provider=='aisstream':
        text=text.replace('around Finnish harbors.','around supported harbors.')
        text=re.sub(r'(    name: Port of Call\n    description: )[^\n]*',
            lambda m:m.group(1)+"See who's coming and going. Observed AIS positions from AISStream; coverage varies. See the maintainer's source and license notes. Optional vessel reference facts from <a href=\"https://www.wikidata.org/\">Wikidata</a> (<a href=\"https://creativecommons.org/publicdomain/zero/1.0/\">CC0</a>). Not for navigation.",text)
    if origin:
        url=urlsplit(origin)
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Polling origin must be HTTPS without credentials, query or fragment')
        text,n=re.subn(r'(?m)^polling_url: ("?)https://[^/\s"]+/api/v1/',
                       lambda m:'polling_url: '+m.group(1)+origin.rstrip('/')+'/api/v1/',text,count=1)
        if n!=1: raise ValueError('Polling URL not found')
    return text
