"""Native workerd smoke test; --live adds real-feed and restart verification."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from check_service import check, get

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'http://127.0.0.1:8790'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    (ROOT/'var').mkdir(exist_ok=True)
    log = (ROOT/'var/cloudflare-runtime.log').open('w')
    process = None
    def stop():
        if process and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    def start(state):
        nonlocal process
        process = subprocess.Popen(['uv', 'run', 'pywrangler', 'dev', '--port', '8790', '--ip', '127.0.0.1',
            '--persist-to', state], cwd=ROOT/'cloudflare', stdout=log, stderr=log, start_new_session=True)
        deadline = time.monotonic()+180
        while time.monotonic() < deadline:
            if process.poll() is not None: raise ValueError('Workers runtime exited; inspect runtime log')
            try:
                if get(ORIGIN+'/')[0] == 200: return
            except Exception: pass
            time.sleep(2)
        raise ValueError('Workers runtime did not start')
    try:
        with tempfile.TemporaryDirectory(prefix='poc-workerd-') as state:
            start(state)
            report = check(ORIGIN, allow_degraded=True, all_framings=True)
            (ROOT/'var/cloudflare-smoke.json').write_text(json.dumps(report, indent=2)+'\n')
            if not report['passed']: raise ValueError('Runtime contract failed')
            print('Native runtime contract passed: 18 snapshots and invalid-route checks')
            if not args.live: return
            deadline = time.monotonic()+240
            while time.monotonic() < deadline:
                status, health, _, _ = get(ORIGIN+'/health')
                if status == 200 and health.get('checkpoint_age_seconds') is not None: break
                time.sleep(5)
            else: raise ValueError('Real collector did not become ready and checkpoint successfully')
            # Allow an initial warming response's 30-second edge cache to expire.
            deadline = time.monotonic()+32
            while time.monotonic() < deadline: time.sleep(min(2, deadline-time.monotonic()))
            report = check(ORIGIN, all_framings=True)
            before = get(ORIGIN+'/api/v1/harbors/helsinki/vessels?spotlight=true')[1].get('focus')
            stop()
            start(state)
            restored = get(ORIGIN+'/api/v1/harbors/helsinki/vessels?spotlight=true')[1].get('focus')
            if before and (not restored or before['mmsi'] != restored['mmsi'] or before['selected_at'] != restored['selected_at']):
                raise ValueError('Subject selection did not survive native runtime restart')
            report['native_restart_passed'] = True
            report['focus_was_available'] = bool(before)
            (ROOT/'var/cloudflare-live.json').write_text(json.dumps(report, indent=2)+'\n')
            if not report['passed']: raise ValueError('Real feed contract/freshness check failed')
            print('Real feed and native SQLite restart passed; aggregate evidence saved')
    finally:
        stop()
        log.close()


if __name__ == '__main__': main()
