"""Local-only TLS-verifying relay for browser tests in a managed proxy environment.
No arbitrary destinations; no credentials are returned. Not part of deployment.
"""
from aiohttp import web, ClientSession, ClientTimeout
from urllib.parse import urlsplit

async def main():
    app = web.Application()
    session = ClientSession(trust_env=True, timeout=ClientTimeout(total=30))
    async def relay(request):
        url = request.query.get('url','')
        parsed = urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname not in ('maps.trmnl.com','trmnl.com','usetrmnl.com') or parsed.username:
            raise web.HTTPForbidden()
        async with session.get(url) as r:
            return web.Response(body=await r.read(), status=r.status,
                                headers={'Content-Type':r.headers.get('Content-Type','application/octet-stream')})
    app.router.add_get('/',relay)
    async def cleanup(app): await session.close()
    app.on_cleanup.append(cleanup)
    return app

web.run_app(main(),host='127.0.0.1',port=8788,access_log=None)
