import asyncio
import json
import logging
import random
import time
import aiohttp
from . import providers
from .model import contains, epoch
from .catalog import verified_harbors, stream_harbors, subscription

log = logging.getLogger('port_of_call.collector')


class Collector:
    def __init__(self, store, config):
        self.store, self.config = store, config
        self.harbors = verified_harbors(config.provider)
        self.connected = False
        self.accepted = self.rejected = 0

    def ingest(self, loc=None, static=None):
        if loc and not any(contains(h['bbox'], loc['position']) for h in self.harbors.values()):
            return False
        self.store.put(loc, static)
        self.accepted += bool(loc)
        return bool(loc)

    async def poll(self, session):
        headers = {'Digitraffic-User': 'PortOfCall/0.1 (shared TRMNL snapshot)', 'Accept-Encoding': 'gzip'}
        now = time.time()
        # Positions are the product: an unavailable static endpoint must not block them.
        async with session.get('https://meri.digitraffic.fi/api/ais/v1/locations', headers=headers) as r:
            r.raise_for_status()
            data = await r.json()
        for feature in data['features']:
            try: self.ingest(providers.digitraffic(feature, time.time(), self.config.ttl))
            except (ValueError, KeyError, TypeError): self.rejected += 1
        self.store.state('last_success', time.time())
        if now-float(self.store.state('metadata_success') or 0) > 3600:
            try:
                async with session.get('https://meri.digitraffic.fi/api/ais/v1/vessels', headers=headers) as r:
                    r.raise_for_status()
                    records = await r.json()
                for record in records:
                    try:
                        static = providers.digitraffic_static(record)
                        if not 0 <= now-static['updated_at'] < 7*86400:
                            raise ValueError('Expired or future metadata')
                        self.store.put(static=static)
                    except (ValueError, KeyError, TypeError): self.rejected += 1
                self.store.state('metadata_success', now)
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError, TypeError) as exc:
                log.warning('metadata_unavailable error=%s', type(exc).__name__)
        self.store.prune(time.time(), self.config.ttl)
        self.connected = True
        self.log_metrics()

    def log_metrics(self):
        now = time.time()
        vessels = self.store.vessels(now, self.config.ttl)
        for h in self.harbors.values():
            reports = [v for v in vessels if contains(h['bbox'], v['position'])]
            age = min((int(now-epoch(v['reported_at'])) for v in reports), default=None)
            log.info('harbor=%s reports=%s latest_age_seconds=%s', h['id'], len(reports), age)

    async def stream(self, session):
        harbors = stream_harbors()
        async with session.ws_connect('wss://stream.aisstream.io/v0/stream', heartbeat=30,
                                      compress=15, max_msg_size=256*1024) as ws:
            await asyncio.wait_for(ws.send_json(subscription(self.config.key, harbors)), timeout=2)
            self.connected = True
            log.info('feed_connected provider=aisstream')
            last_commit = last_metrics = 0
            async for msg in ws:
                if msg.type not in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                    if msg.type == aiohttp.WSMsgType.ERROR: raise ConnectionError('WebSocket error')
                    continue
                try:
                    data = json.loads(msg.data)
                    if 'error' in data: raise ConnectionError('Provider rejected subscription')
                    loc, static = providers.aisstream(data, time.time(), self.config.ttl)
                    accepted = self.ingest(loc, static)
                    # Only real dynamic observations advance feed health.
                    if accepted: self.store.state('last_success', time.time(), commit=False)
                except (ValueError, KeyError, TypeError): self.rejected += 1
                # Commit a batch, not every report: the socket must keep draining.
                if time.time()-last_commit > 5:
                    self.store.prune(time.time(), self.config.ttl)
                    last_commit = time.time()
                if time.time()-last_metrics > 60:
                    self.log_metrics()
                    log.info('stream_reports accepted=%s rejected=%s', self.accepted, self.rejected)
                    last_metrics = time.time()
            raise ConnectionError('Stream closed')

    async def run(self):
        delay = 1
        timeout = aiohttp.ClientTimeout(total=60, sock_connect=15)
        # trust_env preserves the managed proxy and injected authentication.
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            while True:
                try:
                    if self.config.provider == 'digitraffic':
                        await self.poll(session)
                        delay = 1
                        log.info('poll_ok accepted=%s rejected=%s', self.accepted, self.rejected)
                        await asyncio.sleep(self.config.poll_seconds)
                    else:
                        await self.stream(session)
                except asyncio.CancelledError: raise
                except Exception as exc:
                    self.connected = False
                    # No exception URLs/body/headers: a key or proxy token could appear there.
                    log.warning('feed_disconnected provider=%s error=%s retry_seconds=%s',
                                self.config.provider, type(exc).__name__, delay)
                    await asyncio.sleep(delay + random.uniform(0, delay/4))
                    delay = min(delay*2, 300)
