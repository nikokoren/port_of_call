import json
import unittest
from unittest.mock import AsyncMock, patch
from port_of_call.enrichment import Enricher, cached, EnrichmentBudgetExhausted
from port_of_call.memory_store import MemoryStore

NOW = 1793811600.0


class Prefetch(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.clock = [NOW]
        self.e = Enricher(self.store, 'aisstream', clock=lambda: self.clock[0])

    def budget(self, count):
        self.store.state('wikidata_daily_budget', json.dumps(dict(day='2026-11-04', count=count)))

    async def test_empty_and_pending_lists_do_not_waste_hourly_slots(self):
        self.assertEqual(self.e.prefetch('harbor', []), 0)
        self.assertEqual(self.e.prefetch('harbor', ['9000001', '9000002']), 2)
        self.assertEqual(self.e.prefetch('harbor', ['9000001', '9000002', '9000003', '9000004']), 1)
        self.assertEqual(self.e.prefetch('harbor', ['9000004']), 0)
        self.assertEqual(self.e.prefetch_queue.qsize(), 3)
        self.assertEqual(self.e.queue.qsize(), 0)
        self.clock[0] += 3600
        self.assertEqual(self.e.prefetch('harbor', ['9000004', '9000005', '9000006']), 3)

    async def test_shortlist_survives_restart_and_unfinished_work_is_restored(self):
        self.e.prefetch('harbor', ['9000001', '9000002', '9000003'])
        from port_of_call.enrichment import save_cache
        save_cache(self.store, 'ship:9000001', {'facts': []}, NOW, 86400)
        restarted = Enricher(self.store, 'aisstream', clock=lambda: self.clock[0])
        self.assertEqual(restarted.prefetch('harbor', ['9000004']), 0)
        queued = [restarted.prefetch_queue.get_nowait() for _ in range(restarted.prefetch_queue.qsize())]
        self.assertEqual(queued, [('ship', '9000002'), ('ship', '9000003')])

    async def test_visible_card_promotes_a_candidate_without_duplicate_requests(self):
        self.e.prefetch('harbor', ['9000001', '9000002', '9000003'])
        self.e.enqueue({'imo': '9000002'})
        self.e.refresh = AsyncMock()
        while await self.e.process_next(None): pass
        self.assertEqual([c.args[2] for c in self.e.refresh.await_args_list], ['9000002', '9000001', '9000003'])
        self.assertFalse(self.e.pending)

    async def test_display_work_goes_before_speculation_and_has_separate_capacity(self):
        for n in range(20): self.e.prefetch(str(n), [str(9000000+n*3+i) for i in range(3)])
        self.assertEqual(self.e.prefetch_queue.qsize(), 32)
        self.e.enqueue_ports(['ZAQQQ'])
        self.e.refresh = AsyncMock()
        await self.e.process_next(None)
        self.assertEqual(self.e.refresh.await_args.args, (None, 'port', 'ZA QQQ'))

    async def test_reserve_is_rechecked_when_queued_work_runs(self):
        self.e.prefetch('harbor', ['9000001', '9000002', '9000003'])
        self.budget(250)
        self.e.refresh = AsyncMock()
        self.assertFalse(await self.e.process_next(None))
        self.e.refresh.assert_not_awaited()
        self.assertFalse(self.e.pending)
        self.assertIsNone(cached(self.store, 'ship:9000001', NOW))

    async def test_each_http_request_honors_reserve_without_poisoning_negative_cache(self):
        class Body:
            async def iter_chunked(self, size): yield b'{}'
        class Response:
            content = Body()
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def raise_for_status(self): pass
        class Session:
            def __init__(self): self.requests = 0
            def get(self, *args, **kwargs): self.requests += 1; return Response()
        session = Session()
        async def lookup(session, prop, identifier):
            await self.e.request(session, action='query')
            await self.e.request(session, action='wbgetentities')
        self.e.lookup = lookup
        self.e.prefetch('harbor', ['9000001'])
        self.budget(249)
        with patch('port_of_call.enrichment.asyncio.sleep', new=AsyncMock()):
            await self.e.process_next(session)
            self.assertEqual(session.requests, 1)
            self.assertEqual(self.e.remaining_budget(), 250)
            self.assertIsNone(cached(self.store, 'ship:9000001', NOW))
            # Actual screen work can use the reserved requests afterwards.
            await self.e.request(session, action='query')
            self.assertEqual(session.requests, 2)
            self.budget(500)
            with self.assertRaises(EnrichmentBudgetExhausted): await self.e.request(session, action='query')

    async def test_budget_exhaustion_does_not_burn_prefetch_allowance(self):
        self.budget(300)
        self.assertEqual(self.e.prefetch('harbor', ['9000001']), 0)
        self.assertNotIn('harbor', self.e.prefetched)
        self.budget(0)
        self.assertEqual(self.e.prefetch('harbor', ['9000001']), 1)
