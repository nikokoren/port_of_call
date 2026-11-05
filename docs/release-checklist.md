# Release gates

## Implemented and locally verified

- [x] Genuine fresh reports from at least two distinct harbors (Helsinki/Turku; also Rauma); captured fixtures and source metrics retained.
- [x] Longitude/latitude normalization, heading/course fallback, out-of-order/static merges, expiry and bounded outage behavior.
- [x] Shared credential-free Finnish collection, persistence and cached endpoint; no simulated public traffic.
- [x] All four Liquid layouts, all exposed settings and no-data states tested locally.
- [x] Native maps with actual TRMNL vector tiles, visible attribution and genuine historical report previews.
- [x] Synthetic demo is opt-in and labeled; density and outage state fixtures are explicitly identified.
- [x] CI, deployment instructions, license evidence and cost/tradeoff documentation.

Local validation on **5 November 2026**: **52 backend tests**, **20 recipe/label/pixel tests** and **33 browser scenarios** (29 individual layouts/states plus four native mashups with 12 independent map instances). Checks cover independent fact expiry and out-of-order updates, unknown/sentinel values, stable restart-safe subject selection, cooldown, exact free-source identity joins, negative caches/request budgets, Portnet field minimization, escaped payload budgets and protected subject visibility. The browser sweep checks marker projection, an independent connected ship annotation with labels Off, visible text after native clamping, preserved harbor key, permitted context occlusion and card/label/leader clearance, attribution, text bounds and nonblank PNGs.

A real credential-free backend served fresh Spotlight responses for all three Finnish harbors, added cached Wikidata facts on later responses, supplied a reported previous port only for matching actual Portnet calls, and kept the same subjects across scale changes and a process restart. Representative archived Spotlight captures/field-completeness counts are retained separately from the older overview fixtures. Downstream and Hotspots remain unchanged.

The major-port profile retains the genuine secret-backed 900-second coverage evidence: fresh real reports in **13 of 15** areas, with exactly those 13 in its generated form. The richer fields have parser tests, real Finnish capture evidence and a successful 120-second live AISStream follow-up: 833 current per-area observations and 93 eligible subjects in ten areas. Three areas had positions but insufficient static facts in that short cold-start window. Completeness and multi-day reliability remain unproven. Public-rights confirmation and deployment remain separate release gates.

## Required before community submission

- [ ] Deploy a single persistent backend to public HTTPS and verify all catalog endpoints and health externally. **Action:** provision a host/domain and run `docs/deployment.md`; no deployment access was available here.
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
