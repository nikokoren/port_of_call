"""Build a polling form from verified provider coverage, never from candidates."""
import json
import re
from urllib.parse import urlsplit
from .catalog import verified_harbors


def release_settings(text, provider='digitraffic', *, origin=None, registry=None):
    harbors=list(verified_harbors(provider,registry).values())
    if not harbors: raise ValueError('No verified harbors for '+provider+'; candidate ports cannot be packaged')
    block='  - keyname: harbor\n    field_type: select\n    name: Which harbor?\n    options:\n'
    for h in harbors:
        block+='      - '+json.dumps(h['name']+', '+h['country'],ensure_ascii=False)+': '+json.dumps(h['id'])+'\n'
    block+='    default: '+harbors[0]['id']+'\n'
    text,n=re.subn(r'  - keyname: harbor\n.*?(?=  - keyname:|\Z)',block,text,count=1,flags=re.S)
    if n!=1: raise ValueError('Harbor form field not found')
    if provider=='aisstream':
        text=text.replace('around Finnish harbors.','around supported harbors.')
        text=re.sub(r'(    name: Port of Call\n    description: )[^\n]*',
            r'\1See who\u2019s coming and going. Observed AIS positions from AISStream; coverage varies. See the maintainer\u2019s source and license notes. Not for navigation.'.replace('\\u2019',"'"),text)
    if origin:
        url=urlsplit(origin)
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Polling origin must be HTTPS without credentials, query or fragment')
        text=re.sub(r'(?m)^polling_url: .*?/api/v1/harbors/',
                    'polling_url: '+origin.rstrip('/')+'/api/v1/harbors/',text,count=1)
    return text
