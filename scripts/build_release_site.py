"""Build public documentation/downloads; Pages never serves a pretend live feed."""
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from port_of_call.catalog import verified_harbors


def main():
    release = json.loads((ROOT/'deploy/release.json').read_text())
    origin, provider = release.get('origin'), release['provider']
    args = [sys.executable, 'scripts/package_recipe.py', '--provider', provider]
    if origin: args += ['--origin', origin]
    subprocess.run(args, cwd=ROOT, check=True)
    site = ROOT/'site';site.mkdir(exist_ok=True)
    package = 'port-of-call'+('-aisstream' if provider=='aisstream' else '')+'.zip'
    shutil.copy2(ROOT/'dist'/package, site/package)
    shutil.copy2(ROOT/'docs/screenshots/labels-spotlight.png', site/'archived-preview.png')
    (site/'.nojekyll').touch()
    repo = 'https://github.com/nikokoren/port_of_call'
    ports = ', '.join(p['name']+', '+p['country'] for p in verified_harbors(provider).values())
    status = ('Private beta backend · '+html.escape(origin)) if origin else 'Backend deployment pending'
    download = 'Download private-plugin ZIP' if origin else 'Download configuration template (backend setup required)'
    api = '<p><a href="'+html.escape(origin+'/health')+'">Live health</a> · <a href="'+html.escape(origin+'/api/v1/harbors')+'">Supported harbor API</a></p>' if origin else ''
    source = 'Fintraffic / digitraffic.fi · CC BY 4.0' if provider=='digitraffic' else 'AISStream · see documented reuse terms'
    (site/'index.html').write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Port of Call — TRMNL private beta</title>
<style>body{font:17px/1.6 system-ui,sans-serif;max-width:850px;margin:3rem auto;padding:0 1.2rem;color:#17202a}h1,h2{line-height:1.2}a{color:#175c94}img{max-width:100%;height:auto;border:1px solid #ddd}aside{padding:1rem;background:#f1f4f5;border-radius:.5rem}small{color:#48525a}</style>
<h1>Port of Call</h1><p>Harbor maps with genuine vessel positions and an optional connected Ship Spotlight for TRMNL.</p>
<aside><strong>'''+status+'''</strong><br>'''+html.escape(ports)+'''</aside>
<p><a href="'''+package+'">'+download+'''</a></p>'''+api+'''
<h2>Private plugin setup</h2><ol><li>Use a verified deployed backend URL. A configuration template still contains a placeholder.</li><li>Import the six-file ZIP into a TRMNL private plugin.</li><li>Select a harbor and framing; optionally enable vessel names and Spotlight a ship.</li><li>Check every layout and dark mode on your device before sharing a recipe.</li></ol>
<p><a href="'''+repo+'''/blob/main/docs/cloudflare.md">Deployment instructions</a> · <a href="'''+repo+'''/blob/main/docs/release-checklist.md">Release checklist</a> · <a href="'''+repo+'''/issues">Support and source code</a></p>
<h2>Representative screen</h2><img src="archived-preview.png" width="800" height="480" alt="Archived Rauma harbor map with PLYCA Ship Spotlight">
<p><small>Historical AIS capture from 5 November 2026, 09:28 Europe/Berlin. This image is a browser preview, not current traffic or a device photograph.</small></p>
<h2>Sources and limitations</h2><p>'''+html.escape(source)+'''. Optional reference facts use Wikidata (CC0). Map data © OpenStreetMap contributors (ODbL), rendered through TRMNL’s native mapping framework.</p>
<p>AIS coverage is incomplete and can be delayed or inaccurate. Counts describe recent observations near a port. Voyage and ETA fields are crew-entered intentions; missing facts are omitted. Not for navigation.</p>
<p>This is a private beta. Public community submission and physical-device verification are tracked separately. No paid data source or automatic paid hosting upgrade is configured.</p>
</html>''')
    (site/'release.json').write_text(json.dumps(release, indent=2)+'\n')
    print('Built Pages documentation and', package, '; backend', release['status'])


if __name__ == '__main__': main()
