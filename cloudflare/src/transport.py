"""Workers Fetch adapter for the optional enrichment HTTP interface."""
import asyncio
import json
from urllib.parse import urlencode
from workers import fetch


class FetchResponse:
    def __init__(self, url, headers, params):
        self.url = url+('?' + urlencode(params) if params else '')
        self.headers = headers or {}
        self.reader = None
        self.finished = False
        self.content = self

    async def __aenter__(self):
        self.response = await asyncio.wait_for(fetch(self.url, headers=self.headers), timeout=25)
        return self

    def raise_for_status(self):
        if not 200 <= self.response.status < 300: raise ValueError('Upstream HTTP failure')

    async def iter_chunked(self, size):
        self.reader = self.response.body.getReader()
        while True:
            chunk = await self.reader.read()
            if chunk.done:
                self.finished = True
                return
            yield bytes(chunk.value.to_py())

    async def json(self):
        self.raise_for_status()
        data = bytearray()
        async for chunk in self.iter_chunked(65536):
            data.extend(chunk)
            if len(data) > 16_000_000: raise ValueError('Oversized upstream response')
        return json.loads(data)

    async def __aexit__(self, *args):
        if self.reader:
            if not self.finished: await self.reader.cancel()
            self.reader.releaseLock()


class FetchSession:
    def get(self, url, *, headers=None, params=None):
        return FetchResponse(url, headers, params)
