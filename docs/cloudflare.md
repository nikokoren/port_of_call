# Cloudflare free deployment

Cloudflare Workers runs the existing Python validation, snapshot, country/ETA enrichment and Spotlight selection code. One SQLite-backed Durable Object owns the shared collector. GitHub Pages serves documentation and recipe ZIPs; it never substitutes archived JSON or brief Actions samples for a live AIS collector.

## Account setup

1. Create or use a **Workers Free** Cloudflare account. Do not enable Workers Paid or paid add-ons. Set its free `workers.dev` subdomain in Workers settings; no domain purchase is needed.
2. Create an account-scoped API token with **Workers Scripts Edit** and **Account Settings Read** for that account. Add repository secrets **CLOUDFLARE_API_TOKEN** and **CLOUDFLARE_ACCOUNT_ID** in `nikokoren/port_of_call`. Never put credentials in chat, Liquid, a polling URL or Git.
3. The existing **AISSTREAM_API** repository secret is reused by the deployment runner only for an approved AISStream deployment. It is not extracted here. It becomes the Worker secret `AISSTREAM_API_KEY`; the Cloudflare administration token is never sent to the Worker.
4. For AISStream, first record current terms or written permission for the exact public-display/cache use in `deploy/aisstream-rights.json`. Its default remains false. See the [prepared request](aisstream-permission-request.md). The licensed Finnish provider can deploy immediately without an AIS account.

## Deploy

Run **Actions → Deploy Cloudflare backend → Run workflow**, on `main`. Choose `digitraffic` initially, or `aisstream` after its permission record is complete. The workflow tests the shared code, stages only production modules, deploys the Worker and its initial SQLite migration, then waits up to five minutes for real feed readiness. It runs all harbor/framing/Spotlight contract probes before promoting the origin.

On success it records `https://port-of-call.YOUR-SUBDOMAIN.workers.dev` in `deploy/release.json`, produces a six-file plugin ZIP with that origin and the matching provider dropdown, and refreshes Pages downloads. The backend is a **private beta**, not an automatic community submission. The workflow never upgrades the hosting plan.

If deployment succeeded but validation failed, the workflow retains the public URL in its aggregate result artifact without promoting the recipe. Inspect Cloudflare logs and repeat the probe after fixing the cause. No key or raw vessel dataset belongs in artifacts. If repository protections prevent the bot from updating `deploy/release.json`, apply the verified artifact's origin/provider/revision through a normal reviewed commit and rebuild the site.

## What runs

- One Worker and one Durable Object, independent of subscriber count. A five-minute cron starts/restarts the service; one-minute alarms maintain it. AISStream uses one continuous outbound compressed WebSocket and sends its subscription immediately. New requests return warming promptly while collection starts.
- The same 15 KB schema-1 snapshots and settings work on both the Python VM and Cloudflare. All four Liquid layouts remain unchanged.
- Recent positions and per-field facts live in bounded memory. Five-minute checkpoints atomically persist ASCII JSON chunks in SQLite, at most 8 MB. A crash can lose up to five minutes of positions, never refresh their timestamps. Selected subjects and the shared Wikidata daily request budget persist immediately.
- There is one active provider. Checkpoint datasets are separated by provider in the same object's database; immediate code updates close the old collector before starting a new provider. The recipe is rebuilt to match.
- Bounds: 5,000 recent positions, 8,000 metadata records, 1,024 reference records, 512 sanitized Finnish calls and 64 selected ships per harbor. Old metadata is evicted when necessary; missing facts remain missing. No historical voyage tracks, photographs or raw upstream responses are published.
- Public snapshots are cached for 30 seconds at the edge and inside the collector. Public health is uncached. The cache never bypasses the provider's startup permission gate during a fresh deployment; an old edge response may remain for its normal 30-second lifetime.
- Only fixed provider hosts are fetched. Public clients cannot choose upstream URLs, keys or regions. Demo routes are absent. Logs contain aggregate counters and exception classes, never upstream bodies or secret values.

## Free-plan limits and tradeoffs

Verified against Cloudflare's official documentation source on 5 November 2026:

- [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/): 100,000 requests/day on Free, with a 10 ms CPU allowance per Worker invocation.
- [Durable Objects pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/): 100,000 requests/day, 13,000 GB-seconds/day, 5 million SQL rows read/day, 100,000 rows written/day and 5 GB storage. SQLite-backed objects are available on Free. Excess operations fail; the deployment does not add a paid fallback.
- Outbound WebSockets **do not hibernate**. One permanently active 128 MB object accounts for about **11,059 GB-seconds/day** using Cloudflare's published 0.128 GB accounting, consuming most of the 13,000 allowance. Other projects on the same account share its allowances. Do not deploy multiple production collectors on that account without measuring the combined use.
- Incoming WebSocket messages count at a 20:1 billing ratio. A busy source can consume the request allowance even when few TRMNL users are installed. Edge caching reduces origin calls but does not eliminate public Worker requests.
- A fully subscribed device polls 96 times/day at a 15-minute refresh. This is a limited free beta, with capacity to be measured rather than an unlimited-public-service promise. Check CPU, DO duration, incoming message count, memory, storage and request dashboards during the multi-day test.
- Checkpointing is essential: writing every AIS message or every vessel row to durable storage would exceed the free SQL write allowance. The maximum checkpoint is 67 chunks; normal collection writes checkpoints no more often than every five minutes. Request-budget and selection changes add only bounded, low-frequency writes. Runtime crashes/restarts can add writes, so monitor actual usage.

Cloudflare documentation pages returned HTTP 403 in this execution environment; the corresponding official `cloudflare/cloudflare-docs` source was readable. These are published limits, not measured account capacity. Do not claim a completed multi-day study or guaranteed zero-cost capacity before observing the deployed service.

## Verification and operations

`Checks` always builds and starts native `workerd`, testing 18 Finnish scale/Spotlight responses and invalid routes. Dispatch **Checks** with **live=true** for genuine Finnish collection, native SQLite checkpoints and restart/subject recovery. This does not publish vessel data or require hosting credentials. Browser/device checks remain a separate TRMNL gate.

**Live service monitor** is prepared hourly. It starts checking the public origin once `deploy/release.json` contains one. Each run checks all configured harbors, three framings and Spotlight on/off, freshness, positions, payload budgets, source alignment, disabled demo routes and error handling. Only aggregate counts/statuses go into 30-day artifacts. A failure marks the workflow failed; enable GitHub Actions failure notifications for alerts. The first several days of results are still required before community submission.

To run a read-only check manually:

```sh
python scripts/check_service.py https://port-of-call.YOUR-SUBDOMAIN.workers.dev --all-framings
```

Cloudflare manages durable SQLite persistence; use its native recovery/PITR controls for disaster recovery. Never publish checkpoint contents or restore them with altered timestamps. Keep the original VM deployment available as an alternative. For local development, run `python scripts/prepare_cloudflare.py`, then `cd cloudflare && npm ci && uv sync --frozen && uv run pywrangler dev`. This environment blocks the runtime bundle CDN, so native runtime verification runs on GitHub Actions instead.
