# Architecture and decisions

```mermaid
flowchart LR
  D[Digitraffic REST: Finland] --> C[One shared collector]
  A[AISStream: optional persistent WebSocket] -. alternate provider .-> C
  C --> S[(SQLite latest positions + metadata)]
  S --> J[Cached versioned JSON API]
  J --> T[TRMNL polling every 15 minutes]
  T --> M[Liquid + native TRMNLMaps / MapLibre]
```

## Why this architecture

A licensed snapshot API proved viable for a restricted Finnish catalog. Polling it every five minutes is simpler than continuously collecting worldwide events. The ingestion task and HTTP API run in one asynchronous Python process; SQLite/WAL lives on durable local disk. There is no Redis, Worker, scheduler or per-installation subscription. One process per database is required. AISStream position and feed-health writes share a transaction committed about every five seconds; normal shutdown commits pending work, while an abrupt host/process failure can lose the final uncommitted batch. Native map tiles are requested by TRMNL's renderer, not by the backend.

Default settings select only the verified Finnish catalog. IDs are application slugs, **not claimed UN/LOCODE identifiers**. The reviewed versioned registry carries geographic boxes, centers, timezones and provider scope. A bounding rectangle describes an observation area, not an official harbor boundary. Wider uses the full collected box; Standard uses 76% of each dimension and Closer uses 48%. In overview, smaller layouts retain the same known extent. Optional Spotlight frames the current subject with context at the selected scale, while the observed candidate pool remains the reviewed harbor box. `TRMNLMaps.fit` chooses an integer zoom, so additional coastline can appear beyond it.

The alternative AISStream adapter creates one long-lived compressed connection for the verified AISStream catalog (up to the application cap of 15 areas). It sends the subscription immediately, handles binary/text frames, stores last observations and reconnects with exponential backoff/jitter up to five minutes. Do not start multiple replicas: the source documents three subscribed connections/account and three open connections/IP. A short-lived cron sample cannot provide a complete snapshot. The adapter has parser tests and a separate, manually invoked secret-backed coverage probe; deployment still needs account-specific evidence, reviewed map extents and confirmed display rights. See [major-ports.md](major-ports.md).

## Data and freshness

- All coordinate arrays are **[longitude, latitude]**. AISStream subscription corners are explicitly **[latitude, longitude]**.
- MMSI-keyed dynamic and static tables have independent timestamps. Older/equal dynamic observations cannot replace newer ones. Static metadata never moves a vessel or refreshes its position age. Unavailable AIS values (511 heading, 360 course, 102.3 knots) become null.
- No future dynamic timestamps are accepted. Positions at least 60 minutes old are rejected/expired. Names/type metadata older than seven days is removed. Static metadata refreshes hourly and cannot be future dated.
- TimestampExternal in Digitraffic **REST** positions is milliseconds; AIS seconds-within-minute is not a report date. AISStream uses `MetaData.time_utc`; missing dates are rejected rather than invented from receipt time.
- At 30 minutes, old markers become hollow and the area becomes stale if its newest observation is old. A failed poll retains prior data within the bounded window. After 60 minutes without a successful fetch, the endpoint hides all positions and reports unavailable. After an empty successful fetch with no unexpired stored positions it says "No recent vessel reports", never "No ships".
- `snapshot_at` is JSON generation time. `fetched_at` is the last successful provider fetch; `latest_report_at` is the latest observation in the selected area. The API retains both fetch and report local times with timezone abbreviations; the product cards omit these clock rows. Refreshing JSON never re-dates reports.
- Latest positions are pruned on successful polls and reads always enforce expiry, including during an outage. Expired rows on disk can remain until the next successful prune; they cannot reappear on the map.

## Map layout and reusable labels

The layout follows the user’s Downstream recipe: the native `outline` preset fills each view, and a small `bg--canvas outline` information box sits bottom left. Native framework typography, spacing and responsive width classes replace the separate custom header/footer. Framing reserves the area beside or above the box (whichever is larger), using the known harbor bounds and integer zoom. It never follows an outlying vessel or invents an alternate ship location.

The leader-label algorithm was adapted from `nikokoren/hotspots`, `trmnl/src/shared.liquid` (`HSMap.placeLabels`, commit `dba7f701042a81eaaa62a31f200169869256b145`) at the user’s explicit request. Downstream’s framing and native card were taken as the reference from `recipe/src/shared.liquid`, commit `0e89ed63a801a795a05d96e90c6722631c697d6a`. Both source checkouts remain unchanged. The label planner is embedded in Shared so the import still needs only six files; it has pure geometry tests as well as final-pixel browser checks. Exact segment/rectangle intersection improves on sampled leader checks for narrow obstacles. All custom CSS concerns geographic overlays, stacking or link inheritance; presentation uses native framework classes.

## API and limits

`GET /api/v1/harbors` lists the active provider's registry. `GET /api/v1/harbors/{id}/vessels?scale=closer|standard|wider` returns schema version 1. Unsupported IDs return 404; invalid scales return 400. `GET /health` reports readiness/counters and no credentials. `GET /demo/api/v1/harbors/{id}/vessels` requires `ENABLE_DEMO=true` and always includes `demo:true` and a synthetic source. Public routes cannot access fixtures.

Snapshots contain port, viewport, source/attribution, status/message, freshness timestamps, total/shown/omitted counts and normalized vessels. Vessel fields: MMSI, optional name/type, position, reported_at, nullable heading/course/speed, selected bearing and stale flag. 40 vessels maximum; deterministic spatial round-robin favors distribution and recency rather than one dense berth. Responses must fit 20 KB, normally below 15 KB. The UI performs additional pixel-space decluttering and announces its shown/total count. Hidden markers are not reported as absent vessels. Names are optional in every layout, capped at six in full, four in halves and two in quadrants. Label placement reuses Hotspots’ four adjacent candidates, then seven distances along sixteen directions with a leader line. Text and leaders avoid all retained ship glyphs, the information box, attribution and already placed labels. Names are omitted if no safe position fits; the vessel itself never moves.

JSON is shared in 30-second buckets, with 30-second public caching, ETags and at most 60 seconds of downstream stale-if-error tolerance. The in-process cache has at most 64 keys. A 120 requests/minute/IP limiter bounds traffic with at most 4,096 in-memory client buckets. Do not trust arbitrary forwarded IP headers; if placing behind a shared reverse proxy, add a provider edge limiter/cache for scale. Per-IP limits are coarse abuse protection, not an authentication mechanism.

## Security and operation

No user identifiers or vessel history are retained. IP rate counters are transient; HTTP access logging is disabled. Logs contain provider state, aggregate accepted/rejected counts, per-harbor counts/report age and exception class, never upstream response bodies, API keys or headers. SQLite cache is operational data, not a historical tracking service.

Secrets are server-side environment bindings. No credentials are needed by Finnish recipe users. Input scales/harbors are allowlisted, names are bounded/control-character stripped, Liquid attributes escaped and labels inserted as textContent. JSON never embeds markup. No arbitrary backend URL is accepted by the public API.

One active backend serves many devices. Back up SQLite with its online backup API; do not copy an active main file without its WAL. When changing providers, use a new database: source binding prevents attribution mixing. Monitor health, report ages, counters, disk and request volume. Restart persistence is tested. Hosting failover, load testing and a multi-day coverage/uptime study remain deployment checks.

## Extension boundaries

The normalization layer does not depend on TRMNL and the snapshot has `display_mode: map`. Add separately licensed port-call adapters and `/port-calls` without inferring schedules from position history. Spotlight is now an optional Map setting, using validated field-level facts, bounded persistent selection history and cached free enrichment. Its subject is reserved before response truncation. The board control stays hidden until real schedules work. See [Ship Spotlight](ship-spotlight.md). Avoid adding fake ETAs, flag facts or generated voyage claims to the position model.

## Spotlight API and storage

`?spotlight=true` enables shared ship focus (`false`/empty is overview; boolean on/off, yes/no and 1/0 are accepted). Invalid values return 400. Cache keys include normalized focus and scale. Existing clients can ignore the additive `focus_requested`, `focus_mode`, `focus_message` and nullable `focus` fields. `focus` carries identity, position/report times, selection window/reason, bounded facts with individual source/time, reported destination/ETA, optional origin, resolved destination and reference enrichment. Overview markers omit rich fact maps to preserve the 15 KB budget; the featured marker is first and never removed by byte trimming.

Existing SQLite databases migrate additively on startup: `vessel_facts`, `focus_current`, `focus_history`, `enrichment` and `port_calls`. No reset or position replay is needed. All request-time reads enforce expiry during outages. One asynchronous free-enrichment worker uses a bounded deduplicated queue and persisted request budget. Portnet and Wikidata failures are isolated from the position collector. The server needs outbound HTTPS to `www.wikidata.org` and, for Finnish enrichment, `meri.digitraffic.fi`; no new credentials.

## Independent Spotlight annotation

The bottom-left harbor key and `[data-poc-spotlight]` are independent native cards. The extended-label planner shares the Hotspots geometry helpers but treats context hulls as soft obstacles, rather than dropping them to make annotation space. It reserves the featured hull, harbor key and map credit, and always returns a leader line. The regular label pass reserves the resulting card and line. Grey smaller context hulls contrast with the black subject; one-bit contexts use hollow hulls. The API keeps total/shown/omitted information; the visible port-card count describes distinct recent reports in the selected area, including vessels hidden by decluttering or the annotation. The backend payload and shared selection period are unchanged by this presentation revision. See the [ranked content recommendation](ship-spotlight-content.md).

Country-aware enrichment adds `eta_estimate`, provenance-bearing `flag`, optional `registry_country` and `built_in`, and country names on resolved ports/origin. Radio-country lookups use P2979; registry and actual-yard references use P8047/P1071/P176/P17. All remain on the bounded background queue and versioned `v2:` cache. Snapshot generation never performs these network lookups. Existing clients can ignore the additive fields; the byte budget still protects the featured marker. Historical fixtures keep observation time separate from later reference retrieval. See the exact [ETA and country semantics](ship-spotlight.md#country-labels-and-eta-inference--5-november-follow-up).

The accepted native-framework design pass removes the fixed ship-card color/maximum-width overrides. Native `inverse`, responsive auto/min/max width, title/label roles and flex/spacing now govern the annotation's presentation. Geographic placement still measures its rendered dimensions. All metadata shares one native small-label text size, with bold labels and inline labeled dimensions, and the Spotlight SVG connector uses a UI-scale-aware 3px stroke / 7px halo; ordinary label leaders remain unchanged. The port card now follows the requested port/country/count copy, with Fintraffic/source and OpenStreetMap credits in the map footer and optional Wikidata/CC0 credit in About/settings. A native flex row docks the port card and wrapping credits at the bottom edge without credit-driven vertical offsets.

The snapshot adds `focus.presentation` through the pure `display.focus_copy` formatter. It supplies ordered copy from validated source facts, a reported origin/destination story that omits unknown components, preserved zero speed, optional factual highlights and construction/measurement details. Original metadata and provenance remain available alongside it. Service year does not become construction year. Recipe and backend should be upgraded together for the new presentation field. Source links live in author-provided native `.map__attribution` markup; the framework leaves it intact. Its wrapped bounds join the map's protected overlays.

## Cloudflare runtime

The optional [Cloudflare Free deployment](cloudflare.md) reuses the existing Python domain modules. A store interface isolates direct SQL access; `MemoryStore` has snapshot/expiry/rotation parity tests against SQLite. One Durable Object ingests continuously in memory and atomically checkpoints bounded ASCII chunks every five minutes to avoid per-message SQL write quotas. Selection changes and the daily Wikidata budget persist immediately. One-minute alarms plus a five-minute cron handle startup/reconnect; public snapshots never wait for source collection. The public Worker adds a 30-second edge cache. A native workerd CI smoke test exercises the actual Python runtime and SQL bindings. Hosted deployment, actual free-tier usage, AISStream native streaming and multi-day behavior remain deployment checks.
