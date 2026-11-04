"""Private AISStream coverage probe. Counts only; never serves candidate traffic."""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path
import aiohttp
from .catalog import stream_harbors, subscription
from .model import contains, epoch, iso, bearing
from .providers import aisstream
from .store import Store


class Evidence:
    def __init__(self, harbors, started_at):
        self.harbors, self.started_at = harbors, started_at
        self.store = Store(':memory:')
        self.seen = {h['id']:set() for h in harbors}
        self.reports = {h['id']:0 for h in harbors}
        self.received = self.rejected = 0
        self.compression = None
        self.confirmed = self.network_attempted = False

    def observe(self, message, now):
        self.received += 1
        if not isinstance(message, dict):
            self.rejected += 1
            return
        if message.get('MessageType')=='SubscriptionConfirmation':
            self.confirmed = True
            self.compression = message.get('Message',{}).get('CompressionEnabled') is True
            return
        if 'error' in message:
            raise ConnectionError('Provider rejected subscription')
        try:
            loc, static = aisstream(message, now)
            if loc:
                matching = [h for h in self.harbors if contains(h['bbox'],loc['position'])]
                if not matching: return
                for h in matching:
                    self.seen[h['id']].add(loc['mmsi'])
                    self.reports[h['id']] += 1
            if loc or static: self.confirmed = True
            self.store.put(loc, static)
        except (ValueError, KeyError, TypeError): self.rejected += 1

    def report(self, now, outcome, *, connected=False, reason=None):
        observed = connected and self.confirmed
        vessels = self.store.vessels(now,3600)
        rows = []
        for h in self.harbors:
            vs = [v for v in vessels if contains(h['bbox'],v['position'])]
            latest = max((epoch(v['reported_at']) for v in vs),default=None)
            rows.append(dict(id=h['id'],name=h['name'],region=h['region'],bbox=h['bbox'],
                verified=False, observation_attempted=observed,
                distinct_observed=len(self.seen[h['id']]) if observed else None,
                position_reports=self.reports[h['id']] if observed else None,
                current_under_60min=len(vs) if observed else None,
                fresh_under_30min=sum(now-epoch(v['reported_at'])<1800 for v in vs) if observed else None,
                names=sum(bool(v['name']) for v in vs) if observed else None,
                headings=sum(v['heading_deg'] is not None for v in vs) if observed else None,
                courses=sum(v['course_deg'] is not None for v in vs) if observed else None,
                usable_orientation=sum(bearing(v) is not None for v in vs) if observed else None,
                types=sum(v['type'] is not None for v in vs) if observed else None,
                latest_report_at=iso(latest) if latest else None))
        return dict(schema_version=1,provider='AISStream',outcome=outcome,reason=reason,
            started_at=iso(self.started_at),ended_at=iso(now),window_seconds=round(now-self.started_at),
            network_attempted=self.network_attempted,connection_established=connected,subscription_confirmed=self.confirmed,compression_confirmed=self.compression,
            messages_received=self.received,validation_rejects=self.rejected,
            rights_confirmed=False,
            note='Private evaluation only. Counts are observations, not a complete harbor census. No port is automatically verified.',
            harbors=rows)

    def close(self): self.store.close()


async def probe(evidence, key, seconds):
    connected = False
    evidence.network_attempted = True
    started = time.monotonic()
    timeout = aiohttp.ClientTimeout(total=None,sock_connect=15)
    try:
        async with asyncio.timeout(seconds):
            async with aiohttp.ClientSession(trust_env=True,timeout=timeout) as session:
                async with session.ws_connect('wss://stream.aisstream.io/v0/stream',
                        heartbeat=30,compress=15,max_msg_size=256*1024) as ws:
                    connected = True
                    await asyncio.wait_for(ws.send_json(subscription(key,evidence.harbors)),timeout=2)
                    async for msg in ws:
                        if msg.type in (aiohttp.WSMsgType.TEXT,aiohttp.WSMsgType.BINARY):
                            try: message=json.loads(msg.data)
                            except (ValueError,UnicodeError):
                                evidence.rejected+=1
                                continue
                            evidence.observe(message,time.time())
                        elif msg.type==aiohttp.WSMsgType.ERROR: raise ConnectionError('WebSocket failure')
                    return evidence.report(time.time(),'incomplete',connected=True,reason='Stream closed before the collection window completed')
    except TimeoutError:
        complete = time.monotonic()-started >= seconds and evidence.confirmed
        return evidence.report(time.time(),'completed' if complete else 'blocked',connected=connected,
                               reason=None if complete else 'Connection or subscription did not complete the observation window')
    except (aiohttp.ClientError,ConnectionError,OSError) as exc:
        # Never serialize exception text, frame bodies or request URLs: they can contain credentials.
        return evidence.report(time.time(),'incomplete' if evidence.confirmed else 'blocked',connected=connected,
                               reason=type(exc).__name__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true',help='List the 15 candidate areas without network access')
    parser.add_argument('--ports',help='Comma-separated candidate IDs; defaults to all 15')
    parser.add_argument('--seconds',type=int,default=900,help='Collection window: 60–21600 seconds')
    parser.add_argument('--output',default='var/coverage.json')
    args=parser.parse_args()
    if not 60<=args.seconds<=21600: parser.error('--seconds must be between 60 and 21600')
    try: harbors=stream_harbors(args.ports.split(',') if args.ports else None,candidates=True)
    except ValueError as exc: parser.error(str(exc))
    if args.list:
        for h in harbors: print(h['id']+' | '+h['name']+' | '+h['region']+' | '+('data-verified' if h.get('verified') else 'unverified'))
        return
    evidence=Evidence(harbors,time.time())
    try:
        key=os.getenv('AISSTREAM_API_KEY','')
        report=asyncio.run(probe(evidence,key,args.seconds)) if key else evidence.report(
            time.time(),'blocked',reason='Missing AISSTREAM_API_KEY; add it securely to the server environment')
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2)+'\n')
        print(report['outcome']+': '+str(output))
        raise SystemExit(0 if report['outcome']=='completed' else 2)
    finally: evidence.close()


if __name__=='__main__': main()
