"""Build the copy-and-paste guide; Pages never serves a pretend live feed."""
import html
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from port_of_call.catalog import served_harbors


def main():
    release = json.loads((ROOT/'deploy/release.json').read_text())
    origin, provider = release.get('origin'), release['provider']
    site = ROOT/'site';site.mkdir(exist_ok=True)
    for archive in site.glob('*.zip'): archive.unlink()
    shutil.copy2(ROOT/'docs/screenshots/labels-spotlight.png', site/'archived-preview.png')
    (site/'.nojekyll').touch()
    repo = 'https://github.com/nikokoren/port_of_call'
    files = ['custom_fields.yml', 'settings.yml', 'shared.liquid', 'full.liquid',
             'half_horizontal.liquid', 'half_vertical.liquid', 'quadrant.liquid']
    links = ''.join(f'<li><a href="{repo}/blob/main/{name}">{name}</a></li>' for name in files)
    ports = ', '.join(p['name']+', '+p['country'] for p in served_harbors(provider).values())
    status = 'Private beta backend · '+html.escape(origin) if origin else 'Backend deployment pending'
    api = f'<p><a href="{html.escape(origin)}/health">Live health</a> · <a href="{html.escape(origin)}/api/v1/harbors">Supported harbor API</a></p>' if origin else ''
    source = 'Fintraffic / digitraffic.fi · CC BY 4.0' if provider=='digitraffic' else 'AISStream; Finnish ports from Fintraffic / digitraffic.fi, CC BY 4.0'
    (site/'index.html').write_text(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Port of Call — TRMNL private beta</title>
<style>body{{font:17px/1.6 system-ui,sans-serif;max-width:850px;margin:3rem auto;padding:0 1.2rem;color:#17202a}}h1,h2{{line-height:1.2}}a{{color:#175c94}}img{{max-width:100%;height:auto;border:1px solid #ddd}}aside{{padding:1rem;background:#f1f4f5;border-radius:.5rem}}small{{color:#48525a}}</style>
<h1>Port of Call</h1><p>Harbor maps with genuine vessel positions and an optional connected Ship Spotlight for TRMNL.</p>
<aside><strong>{status}</strong><br>{html.escape(ports)}</aside>
<h2>Copy the recipe files</h2><p>Open a GitHub file and use Copy raw file, then paste into its TRMNL editor tab.</p><ul>{links}</ul>{api}
<h2>Private plugin setup</h2><ol><li>Use settings.yml for the live polling URL, GET, 15-minute refresh, framework 3.4.4 and no screen padding.</li><li>Paste all of custom_fields.yml into Custom Fields.</li><li>Paste each Liquid file into its matching Shared, Full, Half Horizontal, Half Vertical or Quadrant editor tab.</li><li>Optionally select harbors (none cycles through all sixteen), ship labels, Spotlight, port facts and the full-screen vessel legend. Save and refresh.</li></ol>
<p><a href="{repo}/blob/main/docs/copy-paste.md">Detailed copy-and-paste guide</a> · <a href="{repo}/blob/main/docs/cloudflare.md">Deployment instructions</a> · <a href="{repo}/blob/main/docs/release-checklist.md">Release checklist</a> · <a href="{repo}/issues">Support and source code</a></p>
<h2>Representative screen</h2><img src="archived-preview.png" width="800" height="480" alt="Archived Rauma harbor map with PLYCA Ship Spotlight">
<p><small>Historical AIS capture from 5 November 2026, 09:28 Europe/Berlin. This image is a browser preview, not current traffic or a device photograph.</small></p>
<h2>Sources and limitations</h2><p>{html.escape(source)}. See documented reuse scope. Optional reference facts use Wikidata (CC0). Map data © OpenStreetMap contributors (ODbL), rendered through TRMNL’s native mapping framework.</p>
<p>AIS coverage is incomplete and can be delayed or inaccurate. Counts describe recent observations near a port. Voyage and ETA fields are crew-entered intentions; missing facts are omitted. Not for navigation.</p>
<p>This is a private beta. Public community submission and physical-device verification are tracked separately. No paid data source or automatic paid hosting upgrade is configured.</p>
</html>''')
    (site/'release.json').write_text(json.dumps(release, indent=2)+'\n')
    print('Built copy-and-paste setup guide; backend', release['status'])


if __name__ == '__main__': main()
