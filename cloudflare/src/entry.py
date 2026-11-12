"""One shared collector; in-memory ingestion and bounded SQLite checkpoints."""
import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from urllib.parse import parse_qs, urlparse
from workers import DurableObject, WorkerEntrypoint, Response, Request, fetch
from js import TextDecoder, caches
from pyodide.ffi import create_proxy
from port_of_call import providers
from port_of_call.catalog import FORWARDED, verified_harbors, stream_harbors, subscription
from port_of_call.enrichment import Enricher, HEADERS
from port_of_call.memory_store import MemoryStore
from port_of_call.model import DEFAULT_SCALE, contains
from port_of_call.rotation import parse_selection, rotate
from port_of_call.snapshot import snapshot
from port_of_call.payload import encode_snapshot
from transport import FetchSession

TTL, CHECKPOINT_SECONDS, CHUNK_SIZE = 3600, 300, 120_000
HEADERS_OUT = {'Content-Type': 'application/json', 'X-Content-Type-Options': 'nosniff', 'Access-Control-Allow-Origin': '*'}


def response(data, status=200, **headers):
    body = None if status == 304 else data if isinstance(data, str) else json.dumps(data, separators=(',', ':'))
    return Response(body, status=status, headers={**HEADERS_OUT, **headers})


class EdgeStore(MemoryStore):
    def __init__(self, sql, provider, payload):
        super().__init__(payload)
        self.sql, self.provider = sql, provider
        sql.exec('CREATE TABLE IF NOT EXISTS control(key TEXT PRIMARY KEY, value TEXT)')
        for key, value in sql.exec('SELECT key,value FROM control').raw().toArray():
            if key in ('wikidata_daily_budget', 'enrichment_prefetch_plans'): self.data['states'][key] = value
            elif key == 'focus:'+provider:
                saved = json.loads(value)
                self.data.update(current=saved['current'], history=saved['history'])

    def state(self, key, value=None, *, commit=True):
        result = super().state(key, value, commit=commit)
        if value is not None and key in ('wikidata_daily_budget', 'enrichment_prefetch_plans'):
            self.sql.exec('INSERT OR REPLACE INTO control VALUES (?,?)', key, str(value))
        return result

    def save_focus(self, *args):
        super().save_focus(*args)
        # Rare subject changes are durable immediately, preserving rotation after
        # an eviction. High-frequency positions still use batched checkpoints.
        value = json.dumps({k: self.data[k] for k in ('current', 'history')}, separators=(',', ':'))
        self.sql.exec('INSERT OR REPLACE INTO control VALUES (?,?)', 'focus:'+self.provider, value)


class Harbor(DurableObject):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.provider = str(env.PROVIDER)
        self.active = verified_harbors(self.provider)
        # Harbors this backend serves by asking another backend (the world
        # backend forwards the Finnish ports to the Finnish Worker), only when
        # the service binding is configured.
        partner = FORWARDED.get(self.provider)
        self.partner = getattr(env, 'FINLAND', None) if partner else None
        self.forwarded = verified_harbors(partner) if partner and self.partner is not None else {}
        self.allowed = bool(self.active) and (self.provider == 'digitraffic' or (
            str(env.AISSTREAM_RIGHTS_CONFIRMED) == 'true' and bool(getattr(env, 'AISSTREAM_API_KEY', ''))))
        self.sql = self.ctx.storage.sql
        self.sql.exec('CREATE TABLE IF NOT EXISTS checkpoint(provider TEXT, part INTEGER, payload TEXT, PRIMARY KEY(provider, part))')
        rows = self.sql.exec('SELECT payload FROM checkpoint WHERE provider=? ORDER BY part', self.provider).raw().toArray()
        payload = ''.join(row[0] for row in rows) if rows else None
        # Release the SQL rows before parsing: a full world checkpoint is several
        # MB, and holding every copy at once pushed restarts past the memory limit.
        del rows
        self.store = EdgeStore(self.sql, self.provider, payload)
        del payload
        self.enricher = Enricher(self.store, self.provider)
        self.session = FetchSession()
        self.socket = None
        self.proxies = []
        self.connected = self.connecting = False
        self.last_message = self.last_maintenance = 0
        self.last_poll = float(self.store.state('positions_poll_at') or 0)
        self.last_checkpoint = float(self.store.state('checkpoint_at') or 0)
        self.retry_at, self.retry_delay = 0, 1
        self.accepted = self.rejected = self.received = 0
        self.last_feed_error = self.close_code = None
        self.lock = asyncio.Lock()
        self.cache = {}
        self.clients = OrderedDict()
        self.started = False

    def checkpoint(self, now):
        self.store.state('checkpoint_at', now)
        body = self.store.checkpoint(now)
        chunks = [body[i:i+CHUNK_SIZE] for i in range(0, len(body), CHUNK_SIZE)]
        def write():
            for part, chunk in enumerate(chunks):
                self.sql.exec('INSERT OR REPLACE INTO checkpoint VALUES (?,?,?)', self.provider, part, chunk)
            self.sql.exec('DELETE FROM checkpoint WHERE provider=? AND part>=?', self.provider, len(chunks))
        callback = create_proxy(write)
        try: self.ctx.storage.transactionSync(callback)
        finally: callback.destroy()
        self.last_checkpoint = now

    def ingest(self, loc=None, static=None):
        if loc and not any(contains(h['bbox'], loc['position']) for h in self.active.values()): return
        self.store.put(loc, static)
        if loc:
            self.store.state('last_success', time.time())
            self.accepted += 1
            self.last_feed_error = None

    def receive(self, event):
        self.last_message = time.time()
        self.received += 1
        try:
            raw = event.data if isinstance(event.data, str) else str(TextDecoder.new().decode(event.data))
            if len(raw) > 256_000: raise ValueError('Oversized AIS frame')
            data = json.loads(raw)
            if data.get('error'):
                # Only publish fixed categories, never upstream text or keys.
                error = str(data['error']).lower()
                self.last_feed_error = ('authentication_rejected' if 'key' in error else
                    'connection_limit' if 'connection' in error else 'subscription_rejected')
                self.disconnect()
                return
            loc, static = providers.aisstream(data, self.last_message)
            self.ingest(loc, static)
        except Exception as exc:
            self.rejected += 1
            self.last_feed_error = "frame:"+type(exc).__name__

    def disconnect(self, *args):
        if args and getattr(args[0], 'type', None) == 'close':
            self.close_code = int(args[0].code)
        socket, self.socket = self.socket, None
        self.connected = False
        if socket:
            for name, callback in zip(('message', 'close', 'error'), self.proxies): socket.removeEventListener(name, callback)
            try: socket.close(1000, 'Reconnect')
            except Exception: pass
        self.retry_at = time.time()+self.retry_delay
        self.retry_delay = min(self.retry_delay*2, 300)

    async def connect(self):
        if self.connecting or self.socket or time.time() < self.retry_at: return
        self.connecting = True
        stage = 'upgrade'
        try:
            for callback in self.proxies: callback.destroy()
            self.proxies = []
            result = await asyncio.wait_for(fetch('https://stream.aisstream.io/v0/stream',
                headers={'Upgrade': 'websocket', 'Sec-WebSocket-Extensions': 'permessage-deflate'}), timeout=20)
            socket = result.js_object.webSocket
            if not socket: raise ValueError('AISStream upgrade rejected')
            self.socket = socket
            stage = 'compression'
            if 'permessage-deflate' not in (result.headers.get('Sec-WebSocket-Extensions') or ''):
                raise ValueError('AISStream compression was not negotiated')
            stage = 'subscribe'
            self.proxies = [create_proxy(self.receive), create_proxy(self.disconnect), create_proxy(self.disconnect)]
            for name, callback in zip(('message', 'close', 'error'), self.proxies): socket.addEventListener(name, callback)
            # Explicitly request ArrayBuffer frames: current Workers runtimes
            # can default to Blob, which TextDecoder.decode cannot consume.
            socket.binaryType = 'arraybuffer'
            socket.accept()
            # No await between accepting and sending the subscription.
            socket.send(json.dumps(subscription(str(self.env.AISSTREAM_API_KEY), stream_harbors())))
            self.connected, self.last_message, self.retry_delay = True, time.time(), 1
        except Exception as exc:
            self.disconnect()
            self.last_feed_error = stage+':'+type(exc).__name__
            print('aisstream_connect_failed', stage, type(exc).__name__)
        finally: self.connecting = False

    async def poll(self, now):
        if now-self.last_poll < 300: return
        self.last_poll = now
        self.store.state('positions_poll_at', now)
        try:
            async with self.session.get('https://meri.digitraffic.fi/api/ais/v1/locations', headers=HEADERS) as r:
                data = await r.json()
            for feature in data['features']:
                try: self.ingest(providers.digitraffic(feature, time.time()))
                except (ValueError, KeyError, TypeError): self.rejected += 1
            self.store.state('last_success', time.time())
            self.connected = True
        except Exception as exc:
            self.connected = False
            print('digitraffic_positions_failed', type(exc).__name__)
            return
        if now-float(self.store.state('metadata_success') or 0) < 3600: return
        try:
            async with self.session.get('https://meri.digitraffic.fi/api/ais/v1/vessels', headers=HEADERS) as r:
                records = await r.json()
            for record in records:
                try:
                    static = providers.digitraffic_static(record)
                    if 0 <= now-static['updated_at'] < 7*86400: self.store.put(static=static)
                except (ValueError, KeyError, TypeError): self.rejected += 1
            self.store.state('metadata_success', now)
        except Exception as exc: print('digitraffic_metadata_failed', type(exc).__name__)

    async def tick(self):
        async with self.lock:
            if not self.allowed:
                self.disconnect()
                await self.ctx.storage.deleteAlarm()
                return
            now = time.time()
            await self.ctx.storage.setAlarm(int((now+60)*1000))
            if self.provider == 'aisstream':
                if self.socket and now-self.last_message > 120: self.disconnect()
                await self.connect()
            else: await self.poll(now)
            self.last_maintenance = now
            self.store.prune(time.time(), TTL)
            await self.enricher.portnet(self.session)
            # A polling object may be evicted while idle. Reconstruct optional
            # work from durable subjects rather than relying on an in-memory queue.
            for port in self.active.values():
                if self.store.current_focus(port['id']):
                    self.enricher.enqueue(snapshot(self.store, port, time.time(), spotlight=True).get('focus'))
            self.enricher.plan_prefetch(self.active)
            await self.enricher.process_next(self.session)
            if time.time()-self.last_checkpoint >= CHECKPOINT_SECONDS: self.checkpoint(time.time())

    async def alarm(self): await self.tick()

    async def forward(self, harbor, scale, focus, fact_period=3600, map_mode=False):
        """The partner backend's snapshot for one of its harbors, or None."""
        url = ('https://partner.internal/api/v1/harbors/'+harbor+'/vessels?scale='+scale+
               '&spotlight='+('true' if focus else 'false')+('&format=map' if map_mode else ''))
        try:
            result = await self.partner.fetch(url)
            if result.status != 200: return None
            data = json.loads(await result.text())
            if data.get('port', {}).get('id') != harbor: return None
            from port_of_call.port_facts import port_fact
            from port_of_call.landmarks import landmarks_for
            data['port_fact'] = port_fact(harbor, time.time(), fact_period)
            data['landmarks'] = landmarks_for(harbor, data['port_fact']['id'] if data['port_fact'] else None)
            return encode_snapshot(data)
        except Exception as exc:
            print('partner_unavailable', type(exc).__name__)
            return None

    async def fetch(self, request):
        if not self.allowed: return response({'error': 'Provider configuration or public-use permission missing'}, 503)
        now = time.time()
        path = urlparse(request.url).path
        if path == '/_tick':
            await self.tick()
            return response({'status': 'started'})
        if not self.started or now-self.last_maintenance > 120:
            if not await self.ctx.storage.getAlarm():
                await self.ctx.storage.setAlarm(int(now*1000)+1)
            self.started = True
        if path == '/health':
            last = float(self.store.state('last_success') or 0)
            ready = bool(last and now-last < TTL)
            return response(dict(status='ready' if ready else 'degraded', provider=self.provider,
                feed_connected=self.connected, last_success_age_seconds=int(now-last) if last else None,
                accepted=self.accepted, rejected=self.rejected, received=self.received,
                last_message_age_seconds=int(now-self.last_message) if self.last_message else None,
                last_feed_error=self.last_feed_error, close_code=self.close_code,
                checkpoint_age_seconds=int(now-self.last_checkpoint) if self.last_checkpoint else None),
                200 if ready else 503, **{'Cache-Control': 'no-store'})
        if path == '/api/v1/harbors':
            return response({'harbors': list(self.active.values()), 'forwarded': list(self.forwarded),'capabilities':{'compact_map':True,'map_candidate_limit':80,'device_cameras':True}},
                            **{'Cache-Control': 'public, max-age=3600'})
        if path == '/api/v1/destination-review':
            from port_of_call.destination_review import report
            return response(report(self.store,now), **{'Cache-Control':'public, max-age=1800'})
        parts = path.strip('/').split('/')
        query = parse_qs(urlparse(request.url).query, keep_blank_values=True)
        if path == '/api/v1/vessels':
            # Recipe endpoint: zero, one or several harbors; several rotate per refresh.
            chosen = parse_selection(query.get('harbors', [''])[0], {**self.active, **self.forwarded})
            harbor = rotate(chosen, now)
            scale = DEFAULT_SCALE
        elif len(parts) == 5 and parts[:3] == ['api', 'v1', 'harbors'] and parts[4] == 'vessels' and (parts[3] in self.active or parts[3] in self.forwarded):
            chosen = [parts[3]]
            harbor, scale = parts[3], query.get('scale', [DEFAULT_SCALE])[0]
        else:
            return response({'error': 'Not found'}, 404)
        raw_focus = query.get('spotlight', ['false'])[0].lower()
        wire_format=query.get('format',['legacy'])[0].lower()
        if wire_format not in ('legacy','map'):return response({'error':'Unknown format'},400)
        map_mode=wire_format=='map'
        if scale not in ('harbor', 'closer', 'standard', 'wider') or raw_focus not in ('', 'true', 'false', 'on', 'off', 'yes', 'no', '1', '0'):
            return response({'error': 'Unknown scale or spotlight value'}, 400)
        client = request.headers.get('CF-Connecting-IP') or 'shared'
        minute = int(now//60)
        count, period = self.clients.pop(client, (0, minute))
        count = count+1 if period == minute else 1
        self.clients[client] = (count, minute)
        while len(self.clients) > 4096: self.clients.popitem(last=False)
        if count > 120: return response({'error': 'Too many requests'}, 429, **{'Retry-After': '60'})
        focus = raw_focus in ('true', 'on', 'yes', '1')
        fact_period = max(3600, len(chosen)*900)
        if harbor in self.forwarded:
            body = await self.forward(harbor, scale, focus, fact_period,map_mode)
            if body is not None:
                return response(body, **{'Cache-Control': 'public, max-age=30'})
            # The partner is unavailable: keep rotating through this backend's
            # own harbors when the selection has any, else report the outage.
            own = [k for k in chosen if k in self.active]
            if not own: return response({'error': 'Harbor feed unavailable'}, 503, **{'Cache-Control': 'no-store'})
            harbor = rotate(own, now)
        key = (harbor, scale, focus, fact_period,map_mode, int(now//30))
        if key not in self.cache:
            if len(self.cache) >= 96: self.cache.clear()
            payload = snapshot(self.store, self.active[harbor], now, scale=scale, spotlight=focus, fact_period=fact_period,map_mode=map_mode)
            self.enricher.enqueue(payload.get('focus'))
            self.enricher.enqueue_ports(payload.pop('unresolved_ports', []))
            self.cache[key] = encode_snapshot(payload,map_mode=map_mode)
        body = self.cache[key]
        etag = '"'+hashlib.sha256(body.encode()).hexdigest()[:24]+'"'
        headers = {'Cache-Control': 'public, max-age=30', 'ETag': etag}
        if request.headers.get('If-None-Match') == etag: return response('', 304, **headers)
        return response(body, **headers)


class Default(WorkerEntrypoint):
    def stub(self): return self.env.HARBOR.get(self.env.HARBOR.idFromName('shared-v1'))

    async def fetch(self, request):
        if request.method not in ('GET', 'HEAD'): return response({'error': 'Method not allowed'}, 405)
        path = urlparse(request.url).path
        if path == '/':
            return response({'name': 'Port of Call', 'catalog': '/api/v1/harbors', 'vessels': '/api/v1/vessels?harbors=', 'health': '/health',
                             'source': 'https://github.com/nikokoren/port_of_call', 'notice': 'AIS is incomplete and delayed. Not for navigation.'})
        if path not in ('/health', '/api/v1/vessels', '/api/v1/destination-review') and not path.startswith('/api/v1/harbors'): return response({'error': 'Not found'}, 404)
        cache = getattr(caches, 'default')
        if path.endswith('/vessels'):
            cached = await cache.match(request.js_object)
            if cached: return Response(cached)
        try: result = await self.stub().fetch(request)
        except Exception as exc:
            print('collector_unavailable', type(exc).__name__)
            return response({'error': 'Collector unavailable'}, 503, **{'Cache-Control': 'no-store'})
        if path.endswith('/vessels') and result.status == 200:
            await cache.put(request.js_object, result.js_object.clone())
        return result

    async def scheduled(self, controller, env, ctx):
        await self.stub().fetch(Request('https://collector.internal/_tick'))
