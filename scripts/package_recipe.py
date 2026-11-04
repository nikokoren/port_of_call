"""TRMNL import zip: put exactly the six export files at archive root."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
Path('dist').mkdir(exist_ok=True)
with ZipFile('dist/port-of-call.zip','w', ZIP_DEFLATED) as z:
    for name in ['settings.yml','shared.liquid','full.liquid','half_horizontal.liquid','half_vertical.liquid','quadrant.liquid']:
        z.write(name)
print('dist/port-of-call.zip — set the deployed polling origin before importing')
