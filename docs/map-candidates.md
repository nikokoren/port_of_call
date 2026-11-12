# More vessels without a crowded map

The recipe now requests up to **80 genuine vessel candidates**, instead of 40. More candidates give the screen more useful choices; the screen still hides overlapping, out-of-frame and covered hulls. It does not promise 80 visible ships.

The backend packs the display fields into compact records rather than repeating JSON keys. The same 15,000-byte limit applies. The shared AIS collectors, free hosting, map camera, hull sizes, heading behavior, spacing and name quotas remain unchanged. No per-vessel external request is added to snapshot generation. Rich Spotlight details and their provenance are retained.

## Same-capture Seattle comparison

These are **historical browser previews**, not current traffic or device photographs. Both limits use identical real observations, timestamps and fixed camera settings. The 40-candidate panel uses the first 40 candidates from the same response; it is not a different day's screenshot. Geometry checks verify matching source positions, matching camera, original timestamps, count text, label/leader clearance and attribution.

Overview source: [actual API response](../fixtures/seattle-candidates.json), **12 November 2026, 09:19:04 CET** (08:19:04 UTC), 80 candidates, 9,645 bytes. The count of 451 describes its observation area, including candidates outside the final screen. Spotlight uses its own [actual response](../fixtures/seattle-candidates-spotlight.json), **09:19:41 CET** (08:19:41 UTC), 80 candidates, 11,049 bytes, with RHONDAVOUS selected. Each comparison pair uses only its corresponding capture.

| View | Visible with 40 candidates | Visible with 80 candidates | Name labels |
|---|---:|---:|---:|
| OG full screen | 18 | 21 | 8 |
| X full screen | 27 | 37 | 16 |
| X portrait | 26 | 33 | 16 |
| OG half horizontal | 11 | 12 | 4 |
| OG half vertical | 6 | 7 | 4 |
| OG quadrant | 5 | 6 | 2 |
| X portrait quadrant | 5 | 6 | 4 |
| OG Spotlight | 18 | 23 | 8 |
| X Spotlight | 27 | 37 | 16 |

[OG before](screenshots/candidates-og-40.png) · [OG after](screenshots/candidates-og-80.png) · [X before](screenshots/candidates-x-40.png) · [X after](screenshots/candidates-x-80.png) · [Portrait after](screenshots/candidates-portrait-80.png) · [Spotlight after](screenshots/candidates-spotlight-80.png).

The algorithm reserves up to 64 slots for the original harbor core, including Spotlight when enabled, then uses remaining slots for its surrounding coverage. That gives larger and portrait screens genuine fixes near their edges without moving the map. Capacity is backfilled from the core if the fringe has fewer observations. Both map and legacy formats use the existing spatial round-robin and interest score. Observation bounds stay inside the collected coverage; the wider map-format area count can differ from a legacy response. The on-map count is measured after drawing and occlusion.

## Verification and updating

- 171 Python tests and 40 JavaScript tests pass, including format compatibility, original timestamps, zero/false values, Unicode byte budgets and all four Liquid layouts.
- 56 existing individual browser cases and four native mashups (twelve independent map instances) pass. Twenty additional comparison panels cover all layouts, portrait, Spotlight and dark mode with the compact records. The comparison exports X full-screen PNGs at 1872×1404 and portrait at 1404×1872; the native framework supplies the scale.
- Native Workers runtime validation passes 30 snapshot configurations. Both deployed services pass 160 live configurations: 128 legacy and 32 compact, plus recipe selection and Finnish forwarding checks. Compact responses in that sweep reached at most 12,944 bytes. These counts and sizes describe this verification run, not a guaranteed traffic density.
- The complete probe respects one bounded `Retry-After` for HTTP 429 because checking both formats can exceed the public per-minute rate limit. Other HTTP failures remain failures.

To reproduce the browser comparison, start the preview and asset-relay servers documented in [README](../README.md), then run:

```sh
PLAYWRIGHT_EXECUTABLE_PATH=/usr/bin/chromium MAP_RELAY=true node scripts/compare-candidates.mjs
```

Results, original source IDs/timestamps, camera values and geometry measurements are retained in [results-candidates.json](screenshots/results-candidates.json). The historical fixtures never become production inputs.

Follow the [copy/paste instructions](copy-paste.md): update **Shared and all four layouts first**, then append `&format=map` to the polling URL. The new templates accept both responses. Existing URLs keep schema 1 and 40 object candidates; the new URL requests schema 2 and up to 80 compact candidates. No custom-field, credential or hosting changes are required.
