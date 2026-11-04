"""TRMNL import zip: six root files, harbor menu limited to verified coverage."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from port_of_call.recipe import release_settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',choices=['digitraffic','aisstream'],default='digitraffic')
    parser.add_argument('--origin',help='Deployed HTTPS backend origin')
    args=parser.parse_args()
    try: settings=release_settings(Path('settings.yml').read_text(),args.provider,origin=args.origin)
    except ValueError as exc: parser.error(str(exc))
    Path('dist').mkdir(exist_ok=True)
    name='port-of-call'+('-aisstream' if args.provider=='aisstream' else '')+'.zip'
    with ZipFile(Path('dist')/name,'w',ZIP_DEFLATED) as z:
        z.writestr('settings.yml',settings)
        for name in ['shared.liquid','full.liquid','half_horizontal.liquid','half_vertical.liquid','quadrant.liquid']:
            z.write(name)
    print('Created recipe archive; verify its HTTPS polling origin before importing')


if __name__=='__main__': main()
