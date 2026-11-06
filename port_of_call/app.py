import asyncio
import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from contextlib import suppress
from dataclasses import dataclass
from aiohttp import web
from .collector import Collector
from .model import HARBORS
from .catalog import verified_harbors
from .snapshot import snapshot
from .store import Store
from .enrichment import Enricher
from .payload import encode_snapshot
from .model import DEFAULT_SCALE
from .rotation import parse_selection, rotate


@dataclass
class Config:
    provider: str = 'digitraffic'
    db_path: str = 'var/positions.sqlite3'
    fresh: int = 1800
    ttl: int = 3600
    poll_seconds: int = 300
    key: str = ''
    demo: bool = False
    rights: bool = False

    def __post_init__(self):
        if self.provider not in ('digitraffic', 'aisstream'): raise ValueError('Unknown provider')
        if not 60 <= self.fresh < self.ttl <= 86400: raise ValueError('Require 60 <= FRESH_SECONDS < EXPIRE_SECONDS <= 86400')
        if self.poll_seconds < 60: raise ValueError('POLL_SECONDS must be at least 60')
        if self.provider == 'aisstream' and (not self.key or not self.rights):
            raise ValueError('AISStream requires AISSTREAM_API_KEY and AISSTREAM_RIGHTS_CONFIRMED=true')

    @classmethod
    def env(cls):
        return cls(provider=os.getenv('PROVIDER','digitraffic'), db_path=os.getenv('DB_PATH','var/positions.sqlite3'),
                   fresh=int(os.getenv('FRESH_SECONDS','1800')), ttl=int(os.getenv('EXPIRE_SECONDS','3600')),
                   poll_seconds=int(os.getenv('POLL_SECONDS','300')), key=os.getenv('AISSTREAM_API_KEY',''),
                   demo=os.getenv('ENABLE_DEMO')=='true', rights=os.getenv('AISSTREAM_RIGHTS_CONFIRMED')=='true')


def create_app(config=None, *, store=None, collect=True, clock=time.time):
    config = config or Config.env()
    active = verified_harbors(config.provider)
    if not active:
        raise ValueError("No verified harbors for this provider; run the coverage probe and review the catalog first")
    own_store = store is None
    store = store or Store(config.db_path)
    bound = store.state('provider')
    if bound and bound != config.provider:
        raise ValueError('Use a separate DB_PATH for each provider')
    store.state('provider', config.provider)
    collector = Collector(store, config)
    enricher = Enricher(store, config.provider, clock=clock)
    cache, clients = {}, OrderedDict()

    @web.middleware
    async def guards(request, handler):
        if request.path != '/health':
            # Do not trust X-Forwarded-For. At a proxy, use its edge rate limiter as well.
            key = request.remote or 'unknown'
            minute = int(clock()//60)
            count, period = clients.pop(key, (0, minute))
            count = count+1 if minute == period else 1
            clients[key] = (count, minute)
            while len(clients) > 4096: clients.popitem(last=False)
            if count > 120:
                return web.json_response({'error':'Too many requests'}, status=429, headers={'Retry-After':'60'})
        try: response = await handler(request)
        except web.HTTPException as e:
            response = web.json_response({'error': e.reason}, status=e.status)
        response.headers.update({'X-Content-Type-Options':'nosniff', 'Access-Control-Allow-Origin':'*'})
        return response

    app = web.Application(middlewares=[guards], client_max_size=1024)

    async def health(request):
        last = float(store.state('last_success') or 0)
        ready = bool(last and clock()-last < config.ttl)
        return web.json_response(dict(status='ready' if ready else 'degraded', provider=config.provider,
            feed_connected=collector.connected, last_success_age_seconds=int(clock()-last) if last else None,
            accepted=collector.accepted, rejected=collector.rejected), status=200 if ready else 503,
            headers={'Cache-Control':'no-store'})

    async def harbors(request):
        return web.json_response({'harbors':list(active.values())},
                                 headers={'Cache-Control':'public, max-age=3600'})

    def spotlight_flag(request):
        raw_focus = request.query.get('spotlight', '').lower()
        if raw_focus not in ('', 'true', 'false', 'on', 'off', 'yes', 'no', '1', '0'):
            raise web.HTTPBadRequest(reason='Unknown spotlight value')
        return raw_focus in ('true', 'on', 'yes', '1')

    def respond(request, mid, scale, spotlight, demo=False):
        port = HARBORS[mid]
        key = (mid, scale, demo, spotlight, int(clock()//30))
        if key not in cache:
            if len(cache) >= 64: cache.clear()
            if demo:
                from .demo import demo_store
                ds = demo_store(port, clock())
                payload = snapshot(ds, port, clock(), config.fresh, config.ttl, scale, True, spotlight)
                ds.close()
            else:
                payload = snapshot(store, port, clock(), config.fresh, config.ttl, scale, spotlight=spotlight)
                if collect: enricher.enqueue(payload.get('focus'))
            body = encode_snapshot(payload).encode()
            cache[key] = body
        body = cache[key]
        headers = {'Cache-Control':'public, max-age=30, stale-if-error=60',
                   'ETag':'"'+hashlib.sha256(body).hexdigest()[:24]+'"'}
        if request.headers.get('If-None-Match') == headers['ETag']: return web.Response(status=304, headers=headers)
        return web.Response(body=body, content_type='application/json', headers=headers)

    async def selection(request):
        # Recipe endpoint: zero, one or several harbors; several rotate per refresh.
        mid = rotate(parse_selection(request.query.get('harbors', ''), active), clock())
        return respond(request, mid, DEFAULT_SCALE, spotlight_flag(request))

    async def vessels(request):
        # Single-harbor endpoint, kept for existing installations and the API.
        mid = request.match_info['port']
        demo = request.path.startswith('/demo/')
        if mid not in HARBORS or (not demo and mid not in active): raise web.HTTPNotFound()
        if demo and not config.demo: raise web.HTTPNotFound()
        scale = request.query.get('scale', DEFAULT_SCALE)
        if scale not in ('harbor','closer','standard','wider'): raise web.HTTPBadRequest(reason='Unknown scale')
        return respond(request, mid, scale, spotlight_flag(request), demo)

    app.router.add_get('/health', health)
    app.router.add_get('/api/v1/harbors', harbors)
    app.router.add_get('/api/v1/vessels', selection)
    app.router.add_get('/api/v1/harbors/{port}/vessels', vessels)
    app.router.add_get('/demo/api/v1/harbors/{port}/vessels', vessels)

    async def lifecycle(app):
        tasks = [asyncio.create_task(collector.run()), asyncio.create_task(enricher.run())] if collect else []
        yield
        for task in tasks: task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError): await task
        store.commit()
        if own_store: store.close()
    app.cleanup_ctx.append(lifecycle)
    return app


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(message)s')
    web.run_app(create_app(), host=os.getenv('HOST','127.0.0.1'), port=int(os.getenv('PORT','8080')),
                access_log=None)  # No persistent visitor/IP history.


if __name__ == '__main__': main()
