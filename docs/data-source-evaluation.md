# Data-source evaluation

Evidence checked **4 November 2026**. These results establish a Finnish private-test implementation, not guaranteed worldwide coverage or an upstream SLA.

## Queries and concrete results

An initial native Git inspection found no commits/project files. Runtime binding metadata and exported variable **names/presence only** were inspected: no AISStream binding/key was available. No credentials were requested or exposed.

Official AISStream documentation was accessible at https://aisstream.io/documentation (the trailing-slash variant returned 403). It confirms server-only keys, immediate subscription within three seconds, three subscribed connections/account and three open connections/IP, replacement subscriptions, binary JSON messages, compression and no durable replay or SLA. No authenticated subscription was possible. The terms pages returned 403; display/redistribution/caching rights therefore remain **unconfirmed**. A free key alone would not establish them.

Digitraffic marine documentation and terms were accessible:

- https://www.digitraffic.fi/en/marine-traffic/
- https://www.digitraffic.fi/en/terms-of-service
- https://meri.digitraffic.fi/api/ais/v1/locations
- https://meri.digitraffic.fi/api/ais/v1/vessels

The API first returned HTTP 406 with the explicit diagnostic `Use of gzip compression is required with Accept-Encoding: gzip header.` Retrying with gzip succeeded (TLS verification retained). Both endpoints returned real reports without credentials. The adapter sends gzip and a `Digitraffic-User` application identifier. The whole-country snapshot is fetched once per poll; only catalog-area positions are persisted. Metadata is fetched once/hour.

Capture: **2026-11-04 17:07:02 UTC (18:07:02 Europe/Berlin)**, genuine positions reported within 30 minutes. This was one REST observation window, not a long-running AIS coverage study. `fixtures/capture-metrics.json` is machine-readable evidence; the three harbor fixtures retain report/fetch dates. The running backend independently fetched a fresh snapshot and served Helsinki with 55 reports, 40 returned and a 9,338-byte JSON response.

| Harbor/area | Source tested | Distinct positions <60m | <30m | Names | Valid heading | Valid course | Classified type |
|---|---|---:|---:|---:|---:|---:|---:|
| Helsinki | Digitraffic REST | 55 | 55 | 55 | 44 | 52 | 53 |
| Turku | Digitraffic REST | 30 | 30 | 29 | 28 | 29 | 29 |
| Rauma (smaller harbor) | Digitraffic REST | 18 | 18 | 17 | 17 | 15 | 17 |
| Hamburg | AISStream: blocked, no key | unmeasured | — | — | — | — | — |
| Rotterdam | AISStream: blocked, no key | unmeasured | — | — | — | — | — |
| Singapore | AISStream: blocked, no key | unmeasured | — | — | — | — | — |

All accepted positions have usable report timestamps and valid geographic coordinates; invalid/future/expired reports are excluded. The Finnish country feed was also filtered against the three international research boxes and contained **zero** reports there, which is outside its promised Finnish coverage. This does not establish that those harbors are empty or that AISStream lacks coverage. Their credentialed verification matrix is deliberately left incomplete.

Two Finnish harbors and the smaller third harbor were demonstrated with genuine data in native-map browser previews. Names are AIS self-reports, not verified identities. Type coverage is imperfect, so category filtering is deferred. Low speed suppresses unreliable COG-based orientation. These thresholds fit a standard 15-minute refresh, but do not guarantee every report arrives in 15 minutes.

## License decision

Fintraffic's terms explicitly license open data **Creative Commons Attribution 4.0**, including commercial distribution/adaptation with attribution, source/license links and notice of changes. The recipe credits `Fintraffic / digitraffic.fi · CC BY 4.0 · filtered`; the JSON also carries attribution links. README/NOTICE explain normalization/selection and retain the accuracy disclaimer. No permission to scrape other sources is inferred.

**Decision:** Ship Finland-first on the proven, openly licensed snapshot API. AISStream is a future optional provider, guarded by a server key and an explicit rights-confirmed deployment flag. Before public use of AISStream, obtain current written terms/confirmation covering caching and public derivative displays/redistribution, the harbor subscription area and account limits. Then run a representative multi-hour collection at Hamburg, Rotterdam, Singapore and a small harbor, report names/heading/types/age completeness, and inspect marker coordinates. Update the dropdown only after evidence. Do not set the rights flag based on these docs.

## Alternatives and economics

API.SH's candidate page returned 403 here; no real snapshot, price or redistribution license was verified. Its approximate/public point locations are unsuitable for precise markers per the supplied specification, so it is not used. VesselFinder/Searoutes require a separately verified commercial offer and data rights; no such access was available. Their current prices or global coverage are not claimed. Official port schedules could be evaluated separately for V2.

Digitraffic is a geographically limited alternative, not a global replacement. Its public terms permit the current derivative display; availability/accuracy are not warranted. At five-minute shared polling, use 288 position requests/day plus 24 metadata requests/day. Sample upstream sizes were roughly one country snapshot, not a harbor request per user. Measure bandwidth on the deployed host before scaling. A modest single-node VM with disk should budget US$5–10/month (planning estimate, not quoted pricing), plus domain/egress. Community recipe screen polls hit the shared small JSON cache; no AIS per-user subscription costs are assumed.

## TRMNL and map verification

Canonical TRMNL/help pages often returned 403 from this machine. The native map documentation was accessible at https://usetrmnl.com/framework/docs/3.4/map/ and the official source repository https://github.com/usetrmnl/trmnl-framework, commit `1aa4dde1436e1359a011093cb5b586f0fc3c0cca`, supplied 3.4.4 runtime/assets and runtime readiness documentation. Form/export syntax was cross-checked against official `usetrmnl/trmnlp` and `usetrmnl/trmnl-form-builder` sources. Local tests interpolate the polling URL and render all Liquid layouts.

Native maps use MapLibre **5.24.0**, `TRMNLMaps.options/watch/fit/ready/settle`, device-aware map paint and `maps.trmnl.com` Shortbread tiles. The docs describe TRMNL's tile source as free to renderers and require visible © OpenStreetMap contributors attribution (ODbL). No public tile.openstreetmap.org raster tiles, scraping or bulk downloads are used. Browser previews fetched actual native vector tiles. JS/CSS preview assets use the pinned official Git sources because canonical asset URLs returned 403 in this environment. That is disclosed rather than treated as a hosted-device test.

Production TRMNL rendering, the canonical hosted asset availability from its renderer, plugin import and physical devices still require the user's account. Verify these before community submission. Screenshot evidence is browser-rendered with real tiles, not a claim that a hosted TRMNL screen or hardware was tested.
