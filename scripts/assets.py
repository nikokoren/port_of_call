"""Fetch pinned official preview assets; production uses TRMNL's hosted runtime."""
from pathlib import Path
import urllib.request
COMMIT = '1aa4dde1436e1359a011093cb5b586f0fc3c0cca'
base = f'https://raw.githubusercontent.com/usetrmnl/trmnl-framework/{COMMIT}/'
assets = {
 'plugins.css':'public/css/3.4.4/plugins.css', 'plugins.js':'public/js/3.4.4/plugins.js',
 'maplibre-gl.js':'vendor/javascript/maplibre-gl-5.24.0.js',
 'maplibre-gl.css':'vendor/javascript/maplibre-gl-5.24.0.css',
}
for font in ('NicoClean-Regular.ttf','Inter.ttf','TRMNL12-Regular.woff2','TRMNL12-Bold.woff2','TRMNL16-Regular.woff2','TRMNL21-Regular.woff2'):
    assets['fonts/'+font] = 'public/fonts/'+font
for name, path in assets.items():
    dest = Path('var/assets')/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        with urllib.request.urlopen(base+path,timeout=60) as r: dest.write_bytes(r.read())
    print(name)
