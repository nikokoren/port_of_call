# Release gates

## Implemented and locally verified

- [x] Genuine fresh reports from at least two distinct harbors (Helsinki/Turku; also Rauma); captured fixtures and source metrics retained.
- [x] Longitude/latitude normalization, heading/course fallback, out-of-order/static merges, expiry and bounded outage behavior.
- [x] Shared credential-free Finnish collection, persistence and cached endpoint; no simulated public traffic.
- [x] All four Liquid layouts, all exposed settings and no-data states tested locally.
- [x] Native maps with actual TRMNL vector tiles, visible attribution and genuine historical report previews.
- [x] Synthetic demo is opt-in and labeled; density and outage state fixtures are explicitly identified.
- [x] CI, deployment instructions, license evidence and cost/tradeoff documentation.

Local validation on 4 November 2026: **23 backend tests, 5 recipe tests and 19 distinct browser scenarios passed** (including the intentionally failed tile-load diagnostic). The final backend was restarted on the persisted database, polled successfully and returned HTTP 200 / `ok` for all three standard harbor endpoints: Helsinki 52 reports / 9,344 bytes; Turku 28 / 6,768 bytes; Rauma 18 / 4,617 bytes. Counts differ from the archived Wider screenshots because time and framing differ. Test logs were observed locally; GitHub Actions has been configured but not run remotely here.

## Required before community submission

- [ ] Deploy a single persistent backend to public HTTPS and verify all catalog endpoints and health externally. **Action:** provision a host/domain and run `docs/deployment.md`; no deployment access was available here.
- [ ] Import the six-file ZIP into a private TRMNL plugin; check form defaults and switching every harbor/scale against your deployed origin. **Action:** use your TRMNL account, replace the placeholder polling origin and test.
- [ ] Confirm canonical MapLibre asset and native tile access from TRMNL's production renderer. Local previews use pinned official assets; some canonical hosts returned 403 to research requests.
- [ ] Test OG (including 1-bit hardware/2-bit previews), X 1872×1404 landscape/1404×1872 portrait, all mashup layouts and light/dark on actual hardware/hosted screenshots. Local Chromium previews are not hardware proof.
- [ ] Run multi-day Finnish coverage/uptime and restart monitoring; sample headings/coordinates against a trusted observation. Publish coverage limitations and a support contact.
- [ ] Review public recipe copy, origin capacity, attribution/source/license links, and settings in the current TRMNL submission UI. Do not claim global coverage or schedules.

## Gates only for worldwide AISStream expansion

- [ ] Secure API key via deployment settings, not chat/markup.
- [ ] Obtain current terms or written confirmation permitting the exact cache/public-display/redistribution use and document any limits/costs.
- [ ] Authenticated representative collection windows for Hamburg, Rotterdam, Singapore and a smaller harbor; record counts, field completeness, report ages and gaps. No real subscription was possible here.
- [ ] Validate parser/message schemas and reconnect/compression on the actual service. Keep one shared subscription and obey account/IP limits.
- [ ] Mark catalog entries verified and update recipe dropdown only after these checks. Do not infer zero traffic from unmeasured coverage.
