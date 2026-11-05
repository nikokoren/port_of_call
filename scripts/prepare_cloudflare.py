"""Stage shared domain code; never copy credentials, fixtures or the VM app."""
from pathlib import Path
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('__init__.py', 'model.py', 'facts.py', 'providers.py', 'catalog.py',
           'snapshot.py', 'spotlight.py', 'display.py', 'enrichment.py',
           'memory_store.py', 'payload.py', 'harbors.json')


def main():
    target = ROOT/'cloudflare/src/port_of_call'
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True)
    for name in MODULES: shutil.copy2(ROOT/'port_of_call'/name, target/name)
    # Wrangler discovers Python modules, not importlib.resources JSON assets.
    # Embed only the canonical registry data; domain algorithms stay identical.
    registry = {h['id']: h for h in json.loads((target/'harbors.json').read_text())}
    (target/'_registry.py').write_text('HARBORS = '+repr(registry)+'\n')
    model = target/'model.py'
    old = "HARBORS = {h['id']: h for h in json.loads(files('port_of_call').joinpath('harbors.json').read_text())}"
    text = model.read_text()
    if old not in text: raise ValueError('Registry packaging entry changed; review the staging script')
    model.write_text(text.replace(old, 'from ._registry import HARBORS', 1))
    print('Staged shared domain code for Cloudflare (no fixtures or secrets)')


if __name__ == '__main__': main()
