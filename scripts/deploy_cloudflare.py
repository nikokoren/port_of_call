"""Deploy the free-plan Worker using secure environment bindings, then verify it."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_service import check, get


def deployment_config(provider):
    if provider not in ('digitraffic', 'aisstream'): raise ValueError('Unknown provider')
    rights = json.loads((ROOT/'deploy/aisstream-rights.json').read_text())
    if provider == 'aisstream':
        if rights.get('confirmed') is not True or not str(rights.get('reference') or '').startswith('https://'):
            raise ValueError('AISStream public use remains blocked: record reviewed terms or written permission in deploy/aisstream-rights.json')
        if not os.environ.get('AISSTREAM_API_KEY'): raise ValueError('Repository secret AISSTREAM_API is required')
    for key in ('CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_API_TOKEN'):
        if not os.environ.get(key): raise ValueError('Missing repository secret '+key)
    return rights


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['digitraffic', 'aisstream'], default='digitraffic')
    args = parser.parse_args()
    deployment_config(args.provider)
    account = os.environ['CLOUDFLARE_ACCOUNT_ID']
    if not re.fullmatch('[a-fA-F0-9]{32}', account): raise ValueError('Invalid Cloudflare account ID')
    request = Request('https://api.cloudflare.com/client/v4/accounts/'+account+'/workers/subdomain',
                      headers={'Authorization': 'Bearer '+os.environ['CLOUDFLARE_API_TOKEN']})
    with urlopen(request, timeout=30) as r: data = json.load(r)
    subdomain = (data.get('result') or {}).get('subdomain')
    if not subdomain or not re.fullmatch('[a-z0-9-]+', subdomain):
        raise ValueError('Create your free workers.dev subdomain in Cloudflare Workers settings first')
    # Keep the original Finnish deployment available for existing installations.
    worker_name = 'port-of-call-world' if args.provider == 'aisstream' else 'port-of-call'
    origin = 'https://'+worker_name+'.'+subdomain+'.workers.dev'
    command = ['uv', 'run', 'pywrangler', 'deploy', '--strict', '--durable-objects-code-update-mode', 'immediate',
               '--name', worker_name, '--var', 'PROVIDER:'+args.provider, '--var', 'AISSTREAM_RIGHTS_CONFIRMED:'+str(args.provider=='aisstream').lower()]
    with tempfile.TemporaryDirectory(prefix='poc-secrets-') as tmp:
        secrets = Path(tmp)/'secrets.json'
        if args.provider == 'aisstream':
            secrets.write_text(json.dumps({'AISSTREAM_API_KEY': os.environ['AISSTREAM_API_KEY']}))
            secrets.chmod(0o600)
            command += ['--secrets-file', str(secrets)]
        result = subprocess.run(command, cwd=ROOT/'cloudflare', text=True, capture_output=True)
        log = result.stdout+result.stderr
        for key in ('CLOUDFLARE_API_TOKEN', 'AISSTREAM_API_KEY'):
            if os.environ.get(key): log = log.replace(os.environ[key], '[redacted]')
        print(log)
        if result.returncode: raise SystemExit(result.returncode)
    (ROOT/'var').mkdir(exist_ok=True)
    result_path = ROOT/'var/deployment-result.json'
    result_path.write_text(json.dumps(dict(origin=origin, provider=args.provider, status='verifying'), indent=2)+'\n')
    # Cold start returns warming promptly; alarm/cron collection runs separately.
    deadline = time.monotonic()+300
    while time.monotonic() < deadline:
        try:
            if get(origin+'/health')[0] == 200: break
        except Exception: pass
        time.sleep(10)
    else: raise ValueError('Worker deployed but feed did not become ready; see the deployment URL and Cloudflare logs')
    report = check(origin, all_framings=True)
    (ROOT/'var/release-check.json').write_text(json.dumps(report, indent=2)+'\n')
    if not report['passed']: raise ValueError('Live validation failed; production recipe metadata was not promoted')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    release = dict(provider=args.provider, origin=origin, status='private-beta', revision=revision, verified_at=report['checked_at'])
    (ROOT/'deploy'/('finland-release.json' if args.provider=='digitraffic' else 'world-release.json')).write_text(json.dumps(release, indent=2)+'\n')
    (ROOT/'deploy/release.json').write_text(json.dumps(release, indent=2)+'\n')
    result_path.write_text(json.dumps(release, indent=2)+'\n')
    subprocess.run(['python', 'scripts/package_recipe.py', '--provider', args.provider, '--origin', origin], cwd=ROOT, check=True)
    print('Deployed and verified', origin, '; private-beta package ready. No community submission was performed.')


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        # Exception URLs/headers from authenticated APIs must not leak credentials.
        print('Deployment stopped:', str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
        raise SystemExit(1)
