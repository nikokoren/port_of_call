"""Print the most common unresolved display terms; uses no AIS credentials."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',action='append',help='Repeat for both backend profiles; defaults to recorded deployments')
    parser.add_argument('--limit',type=int,default=30)
    args=parser.parse_args()
    origins=args.origin or sorted({json.loads(p.read_text())['origin'] for p in Path('deploy').glob('*-release.json')})
    rows=[]
    for origin in origins:
        request=Request(origin.rstrip('/')+'/api/v1/destination-review',headers={'User-Agent':'PortOfCall destination review'})
        with urlopen(request,timeout=30) as r: rows.extend(json.load(r)['terms'])
    rows.sort(key=lambda r:(-r['vessels'],-r['windows'],r['port'],r['term']))
    print('| Harbor | Term | Distinct vessels (capped at 64) | Half-hour windows |')
    print('|---|---|---:|---:|')
    for row in rows[:max(1,args.limit)]:
        print(f"| {row['port']} | {row['term']} | {row['vessels']} | {row['windows']} |")


if __name__=='__main__':main()
