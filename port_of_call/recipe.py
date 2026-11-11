"""Build a polling form from verified provider coverage, never from candidates."""
import json
import re
from urllib.parse import urlsplit
from .catalog import served_harbors, verified_harbors


FACTS = 'Optional vessel reference facts from <a href="https://www.wikidata.org/">Wikidata</a> (<a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>). Not for navigation.'
BIOS = {
    'aisstream': "See who's coming and going. Observed AIS positions from AISStream; coverage varies. Finnish ports from Fintraffic / digitraffic.fi, CC BY 4.0. See the maintainer's source and license notes. "+FACTS,
    'digitraffic': "See who's coming and going. Observed AIS positions, not port schedules. Source Fintraffic / digitraffic.fi, CC BY 4.0; filtered and normalized. "+FACTS,
}


COMMENTS = {
    'aisstream': '# World profile, including Finnish ports. Copy-and-paste guide: docs/copy-paste.md.\n',
    'digitraffic': '# Finnish profile (Fintraffic / Digitraffic backend).\n',
}


def release_settings(text, provider='digitraffic', *, origin=None, registry=None):
    if not verified_harbors(provider,registry): raise ValueError('No verified harbors for '+provider+'; candidate ports cannot be packaged')
    # The menu lists every harbor the backend serves, including forwarded ones.
    harbors=list(served_harbors(provider,registry).values())
    # Keep the hand-written field header (name, help text, multiple/optional)
    # and replace only its options with the verified catalog.
    def label(h): return h['name'] if h['country']==h['name'] else h['name']+', '+h['country']
    options='    options:\n'+''.join('      - '+json.dumps(label(h),ensure_ascii=False)+': '+json.dumps(h['id'])+'\n'
                                  for h in harbors)
    text,n=re.subn(r'(  - keyname: harbor\n(?:(?!  - keyname:|    options:\n).*\n)*)    options:\n(?:      - .*\n)*(?:    default: .*\n)?',
                   lambda m:m.group(1)+options,text,count=1)
    if n!=1: raise ValueError('Harbor form field not found')
    text,n=re.subn(r'(?m)(?:^#[^\n]*\n)*(?=^polling_url: )',lambda m:COMMENTS[provider],text,count=1)
    if n!=1: raise ValueError('Polling URL not found')
    # Each profile credits its own data source; the template may hold either.
    bio=BIOS[provider]
    text,n=re.subn(r'(    name: Port of Call\n    description: )[^\n]*',lambda m:m.group(1)+bio,text,count=1)
    if n!=1: raise ValueError('Author bio not found')
    if origin:
        url=urlsplit(origin)
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Polling origin must be HTTPS without credentials, query or fragment')
        text,n=re.subn(r'(?m)^polling_url: ("?)https://[^/\s"]+/api/v1/',
                       lambda m:'polling_url: '+m.group(1)+origin.rstrip('/')+'/api/v1/',text,count=1)
        if n!=1: raise ValueError('Polling URL not found')
    return text
