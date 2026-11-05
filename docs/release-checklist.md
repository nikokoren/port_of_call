# Release gates

## Implemented and locally verified

- [x] Genuine fresh reports from at least two distinct harbors (Helsinki/Turku; also Rauma); captured fixtures and source metrics retained.
- [x] Longitude/latitude normalization, heading/course fallback, out-of-order/static merges, expiry and bounded outage behavior.
- [x] Shared credential-free Finnish collection, persistence and cached endpoint; no simulated public traffic.
- [x] All four Liquid layouts, all exposed settings and no-data states tested locally.
- [x] Native maps with actual TRMNL vector tiles, visible attribution and genuine historical report previews.
- [x] Synthetic demo is opt-in and labeled; density and outage state fixtures are explicitly identified.
- [x] CI, deployment instructions, license evidence and cost/tradeoff documentation.

Local validation on **5 November 2026**: **78 backend tests**, **24 recipe/label/pixel tests** and **34 browser scenarios** (30 individual layouts/states plus four native mashups with 12 independent map instances). Checks cover independent fact expiry and out-of-order updates, unknown/sentinel values, stable restart-safe subject selection, cooldown, exact free-source identity joins, negative caches/request budgets, Portnet field minimization, escaped payload budgets and protected subject visibility. The browser sweep checks marker projection, an independent connected ship annotation with labels Off, visible text after native clamping, preserved harbor key, permitted context occlusion and card/label/leader clearance, attribution, metadata size consistency, bottom-left card anchoring, text bounds and nonblank PNGs.

A real credential-free backend served fresh Spotlight responses for all three Finnish harbors, added cached Wikidata facts on later responses, supplied a reported previous port only for matching actual Portnet calls, and kept the same subjects across scale changes and a process restart. Representative archived Spotlight captures/field-completeness counts are retained separately from the older overview fixtures. Downstream and Hotspots remain unchanged.

The major-port profile retains the genuine secret-backed 900-second coverage evidence: fresh real reports in **13 of 15** areas, with exactly those 13 in its generated form. The richer fields have parser tests, real Finnish capture evidence and a successful 120-second live AISStream follow-up: 833 current per-area observations and 93 eligible subjects in ten areas. Three areas had positions but insufficient static facts in that short cold-start window. Completeness and multi-day reliability remain unproven. Public-rights confirmation and deployment remain separate release gates.

## Required before community submission

- [x] Deployed and verified the Finnish Cloudflare backend over public HTTPS, including all eighteen harbor/framing/Spotlight combinations. Initial deployment and first public monitor passed; multi-day behavior remains unverified.
- [ ] Import the six-file ZIP into a private TRMNL plugin; check form defaults and switching every harbor/scale against your deployed origin. **Action:** use your TRMNL account, replace the placeholder polling origin and test.
- [ ] Confirm canonical MapLibre asset and native tile access from TRMNL's production renderer. Local previews use pinned official assets; some canonical hosts returned 403 to research requests.
- [ ] Test OG (including 1-bit hardware/2-bit previews), X 1872×1404 landscape/1404×1872 portrait, all mashup layouts and light/dark on actual hardware/hosted screenshots. Local Chromium previews are not hardware proof.
- [ ] Run multi-day Finnish coverage/uptime and restart monitoring; sample headings/coordinates against a trusted observation. Publish coverage limitations and a support contact.
- [ ] Review public recipe copy, origin capacity, attribution/source/license links, and settings in the current TRMNL submission UI. Do not claim global coverage or schedules.

## Gates only for worldwide AISStream expansion

- [x] Repository key used securely in a manual Actions coverage job; it was not extracted or printed. The deployed backend still needs its own secure binding.
- [ ] Obtain current terms or written confirmation permitting the exact cache/public-display/redistribution use and document any limits/costs.
- [x] Authenticated 900-second collection for 15 areas, including Hamburg, Rotterdam, Singapore and comparatively smaller Felixstowe/Harwich. Fresh data in 13; two no-report areas are excluded. Counts and field completeness are retained in `docs/coverage/`. Longer continuity tests remain outstanding.
- [ ] Validate parser/message schemas and reconnect/compression on the actual service. Keep one shared subscription and obey account/IP limits.
- [x] Data-verified only the 13 positive areas and generated their provider-specific private-test dropdown; the separate public-rights flag remains off. Two no-report areas remain unverified. Do not infer zero traffic from unmeasured coverage.

The labeled inverted-overlay follow-up also validates UTC year rollover/leap-day inference, rejection of obsolete/far-future ETAs, MID special-format exclusions, radio-area/country resolution, exact country joins, current registry qualifiers, shipyard-versus-company identification and country-qualified ports. Browser checks assert native inverse contrast in light/dark/one-bit views, readable labeled facts and preserved context-vessel framing in the compact horizontal example.

The native-framework design follow-up uses the requested port/country/count copy and map-level source credits, uses semantic native typography and auto/min/max sizing, uses consistent native small labels and inline dimensions, and strengthens only the Spotlight connector. Its explicit dark and dark one-bit cases exercise native inverse behavior. Unknown-statistic tests cover absent and single-column values; browser geometry also checks metadata type consistency and corner anchoring and the connector's actual stroke width. See [applied design review](spotlight-design-review.md).

The text follow-up validates ordered narrative copy, omission of missing origin/country components, zero speed, independent length/width, source/credit relocation and separation of service-entry versus construction year. Historical-preview provenance is outside the device frame; the original AIS capture timestamps and positions are unchanged. Port counts are scoped observations rather than a port census.

## Prepared release automation

- [x] Cloudflare Python Worker/SQLite Durable Object deployment, sharing the existing domain code and protected public-use gate.
- [x] Bounded in-memory ingestion and atomic checkpoints; immediate durable rotation/budget updates; SQLite parity/restart/expiry tests.
- [x] Native workerd build/start/18-snapshot smoke test on GitHub Actions. The `Checks` live input also passed genuine collection, checkpoints and subject recovery in [run 42104240937](https://github.com/nikokoren/port_of_call/actions/runs/42104240937); this is native workerd on a runner, not a public Cloudflare deployment.
- [x] Manual deployment workflow, generated origin-specific ZIP, hourly live monitor, Pages setup/download site and community-listing draft.
- [x] Cloudflare account/token securely supplied through repository secrets; public Finnish backend deployed and verified in [run 42119720182](https://github.com/nikokoren/port_of_call/actions/runs/42119720182). Its initial Pages job was blocked; the site is now published.
- [x] GitHub Pages Source = GitHub Actions enabled by the user. [Publication 42120540201](https://github.com/nikokoren/port_of_call/actions/runs/42120540201) succeeded; the public HTML, release metadata and six-file ZIP were fetched and verified.
- [ ] Import and verify in the user's private TRMNL plugin. No TRMNL account/plugin credentials were available.
- [ ] Complete several days of live monitoring/quota observation after deployment. An installed hourly monitor is not a completed study.

The current deployment status is machine-readable in `deploy/release.json`; the current origin is a verified private beta. AISStream terms/permission remain separately recorded in `deploy/aisstream-rights.json`. Neither check is bypassed by a working API key or a prepared workflow. See [Cloudflare operations](cloudflare.md) and [submission copy](community-listing.md).

First public monitor: [run 42119977676](https://github.com/nikokoren/port_of_call/actions/runs/42119977676), successful. The six-file ZIP contains the live polling origin and the matching Finnish dropdown. The [public setup/download site](https://nikokoren.github.io/port_of_call/) is live and its ZIP contains the verified Cloudflare polling origin.
