# Port of Call

**Harbor Arrivals & Departures · See who's coming and going.**

A map-first TRMNL recipe showing **observed AIS positions**, not authoritative port schedules. The first catalog is **Helsinki, Turku and Rauma, Finland**. One shared backend serves every installation; users never need AIS keys.

**AIS can be incomplete, delayed and inaccurate. Not for navigation.** A vessel marker is an observation, not proof of an arrival, departure or berth. Hulls point to true heading when available, otherwise course above 0.5 knots; diamonds have no useful orientation. Hollow hulls indicate reports older than 30 minutes. Counts refer to reports within the selected area, not all ships in port.

![Helsinki: genuine historical AIS capture, 4 November 2026](docs/screenshots/og-helsinki.png)

This is a browser preview with native TRMNL vector tiles and **genuine historical AIS**, captured 4 November 2026. It is not current traffic. [All previews and provenance](docs/screenshots/README.md).

## What works

- Gzip-aware shared Digitraffic polling, position/static normalization, SQLite persistence, bounded retention and outage recovery.
- Public JSON API, 30-second response cache, ETags and rate limiting; typical response below 15 KB.
- Native `TRMNLMaps` / MapLibre, geographically anchored hulls, Hotspots-style offset names and leader lines, decluttering and visible OpenStreetMap attribution.
- Downstream-style full maps with a bottom-left information box in full, half-horizontal, half-vertical and quadrant layouts; OG and X landscape/portrait browser previews, including dark mode.
- Harbor, framing, optional vessel names and Map-only display mode settings. Categories are retained internally but not exposed: type coverage is not sufficient to hide unknown vessels confidently.
- An isolated synthetic demo endpoint, disabled by default. Production never loads fixtures.

The catalog is deliberately limited, not the full reach of the Finnish feed: a further live check found reports around Hanko, Kotka, Oulu, Vaasa and Pori. Those candidate areas are not yet reviewed catalog entries.

Public deployment and a hosted TRMNL import/device test are **not yet performed**. No hosting or TRMNL account access was provided. Hamburg, Rotterdam and Singapore are research candidates, excluded from the published dropdown. [Release gates](docs/release-checklist.md).

## Run locally

Python 3.12+; Node 24 is only needed for recipe tests and previews.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/port-of-call
```

No key is needed. The process reads exported variables; it **does not automatically load `.env`**. Safe defaults are in [.env.example](.env.example). The first poll normally takes a few seconds. The SQLite directory is created automatically.

```sh
curl -f http://127.0.0.1:8080/health
curl -f 'http://127.0.0.1:8080/api/v1/harbors/helsinki/vessels?scale=wider'
```

`/health` returns 503 until a successful fetch and when its last success is at least 60 minutes old. The snapshot endpoint still returns a deliberate `warming`, `empty`, `stale` or `unavailable` state. A successful HTTP fetch is distinct from the time of the latest vessel report. Configure `FRESH_SECONDS=1800`, `EXPIRE_SECONDS=3600` and `POLL_SECONDS=300` as needed; fresh must be shorter than expiry. Use a separate `DB_PATH` for each provider.

## Test as a private TRMNL plugin

1. [Deploy the backend](docs/deployment.md) to a public HTTPS origin. Verify `/health` and all three harbor endpoints. A localhost address cannot be polled by hosted TRMNL.
2. Replace **only** `https://YOUR-BACKEND.example` in `settings.yml` with your service origin. Keep `{{ harbor }}` and `{{ map_scale }}` intact.
3. Run `npm ci` then `npm run package`. Import `dist/port-of-call.zip` using TRMNL's private plugin import flow. The ZIP has the six export files at its root. If the UI requires manual setup, use polling/GET/15 minutes, framework **3.4.4**, paste the custom fields YAML and the five Liquid files into their corresponding tabs.
4. Choose a harbor, Standard framing, names Off and Harbor Map. Confirm data loads and change the harbor to verify polling URL interpolation.
5. Test all four layouts, light/dark, and your device. Keep framework-provided map attribution visible. MapLibre JS/CSS load separately, as the native docs require.

The files follow the official CLI/export settings structure. The exact hosted import and physical-device capture remain a release gate; do not advertise them as tested. For a future community recipe, the maintainer fixes the hosted origin in settings before submission; ordinary users do not configure infrastructure.

## Tests and previews

```sh
.venv/bin/python -m unittest discover -s tests -v
npm ci
npm test
npm run package
```

Offline tests use explicitly identified fixtures. To refresh **historical test captures** from the real provider:

```sh
.venv/bin/python scripts/capture_real.py
```

This overwrites the three captured fixtures and their metrics intentionally. Never replay them into production. State-test fixtures deliberately alter the state of a historical capture; demo positions are fully synthetic.

For actual native-map browser screenshots (network required):

```sh
.venv/bin/python scripts/assets.py
npx playwright install chromium
npm run preview
# another terminal
npm run screenshots
# Optional multi-instance layout regression check
node scripts/check-mashups.mjs
```

The pinned preview assets come from the official framework Git commit recorded in `scripts/assets.py`. On managed machines where Chromium must use an HTTP proxy, run `.venv/bin/python scripts/asset_proxy.py` and set `MAP_RELAY=true` for screenshots. This local-only TLS-verifying relay allows only the native TRMNL asset/tile hosts. It is not deployed. `PLAYWRIGHT_BROWSERS_PATH` may select an existing browser installation.

## Sources, rights and cost

The default backend uses [Fintraffic / Digitraffic](https://www.digitraffic.fi/en/marine-traffic/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Positions are validated, filtered and rounded to about one metre; static metadata is joined by MMSI. Attribution, source and license links are in the recipe and API. Data carries no accuracy or availability warranty. Map data: © OpenStreetMap contributors, ODbL; native TRMNL attribution remains visible.

AISStream's adapter is implemented but **not live-tested or cleared for public redistribution**. Its key and `AISSTREAM_RIGHTS_CONFIRMED=true` are required to enable it. Never set that flag just to bypass a license review. [Data evaluation](docs/data-source-evaluation.md) records evidence and exact blockers.

One small always-on Linux server with durable disk is sufficient. Budget roughly **US$5–10/month** for a modest VM, plus domain/egress if charged; this is a planning estimate, not a vendor quote. There is no per-user AIS subscription in the default Finnish workflow. Upstream polling stays at 288 shared location fetches/day and 24 metadata fetches/day, independent of recipe installations. See [architecture](docs/architecture.md), [deployment](docs/deployment.md) and [roadmap](docs/roadmap.md).

Code is MIT licensed. Data and third-party frameworks retain their own licenses; see [NOTICE](NOTICE).
