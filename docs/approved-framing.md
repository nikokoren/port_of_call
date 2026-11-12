# Approved OG and X harbor framings

The maintainer's [exported draft](approved-framing.json), based on revision `c06344e4dc8ebee09b0cae1dd2bd3d85a6e06d40`, is applied exactly to all sixteen harbors. It contains **32 independent cameras**, with the submitted longitude/latitude and integer zoom values preserved. [The registry](../port_of_call/harbors.json) stores them as `cameras.og` and `cameras.x`. The common `focus` and `zoom` remain the approved OG fallback.

| Harbor | OG zoom | X zoom |
|---|---:|---:|
| Helsinki | 12 | 12 |
| Turku | 12 | 12 |
| Rauma | 11 | 12 |
| Rotterdam | 10 | 10 |
| Antwerp | 10 | 11 |
| Hamburg | 11 | 12 |
| Bremerhaven | 11 | 12 |
| Felixstowe | 11 | 12 |
| Southampton | 11 | 11 |
| Los Angeles / Long Beach | 11 | 12 |
| New York / New Jersey | 11 | 11 |
| Savannah | 11 | 11 |
| Houston | 11 | 11 |
| Seattle | 11 | 12 |
| Charleston | 12 | 12 |
| Singapore | 10 | 11 |

## Device selection and compatibility

Compact map responses retain `camera.center` / `camera.zoom` for OG compatibility and add `camera.profiles.og` and `.x`. Each profile contains `center: [longitude, latitude]` and `zoom`. The four Liquid layouts carry the X values alongside the existing OG attributes. Shared selects X using the native screen identity (`--device-name` / `screen--v2`), including half/quadrant mashups; it never infers the device from the smaller map element's width. Existing snapshots without profiles keep their original fallback behavior.

The chosen harbor focus remains in the open part of the map, beside or above the native port card. Card padding can offset the visible map center; it does not change the saved focus. Both profiles keep the existing UI-scale adjustment. Spotlight does not recenter either camera. The legacy response without `format=map` keeps its OG-scoped viewport and 40-marker contract; the current recipe requests the compact map format.

## Vessel coverage and selection

Provider bounding boxes, names, countries, source assignments and other non-camera registry metadata are unchanged; the [source baseline](framing-source-baseline.json) records them for regression checks. The change does not add AIS subscriptions, move an observation, change headings or expand collection coverage.

The shared compact response covers the union of both device observation envelopes, clipped to existing source coverage. Candidate selection alternates the OG and X spatial queues so a crowded wider OG view cannot starve a narrower X view. The first 64 slots cover the device cores, remaining capacity adds surrounding positions for portrait/card offsets, and spare capacity is backfilled from the cores. The existing 80-candidate / 15,000-byte limits and client hull/label decluttering remain.

Spotlight first considers eligible ships in the safe intersection of both views. If there is no eligible shared candidate, either view may supply one, and a layout that cannot display it retains the existing overview fallback. Interest, motion, enrichment and hold/cooldown priorities are unchanged. Background ship-reference prefetch uses the same shared-view eligibility.

## Preview and tests

Native browser checks project each submitted focus back onto the open map area and verify the selected device and exact zoom. They cover all 32 full-screen cameras plus portrait and all compact layouts. [Recorded results](screenshots/results-approved-framing.json). Representative map-only previews:

- [Seattle OG](screenshots/approved-seattle-og.png) / [X](screenshots/approved-seattle-x.png)
- [Helsinki OG](screenshots/approved-helsinki-og.png) / [X](screenshots/approved-helsinki-x.png)
- [Rotterdam OG](screenshots/approved-rotterdam-og.png) / [X](screenshots/approved-rotterdam-x.png)
- [Singapore OG](screenshots/approved-singapore-og.png) / [X](screenshots/approved-singapore-x.png)

These framing references contain **no vessel observations or simulated traffic**. Existing historical AIS fixtures keep their original camera and observation provenance. Python tests verify exact approved values, unchanged provider metadata, both device candidate queues, original fixes, compact/legacy compatibility and shared Spotlight visibility. The native runtime/live monitor checks both camera profiles in compact responses, including Finnish forwarding.

To reproduce the camera checks, run the preview and map-relay servers, then:

```sh
PLAYWRIGHT_EXECUTABLE_PATH=/usr/bin/chromium MAP_RELAY=true node scripts/check-approved-framing.mjs
```

The [framing editor](https://nikokoren.github.io/port_of_call/framing/) now starts from the approved per-device defaults. Existing local draft entries that exactly match these defaults are treated as applied; other pending local edits are retained.

Update **Shared and all four layouts** from GitHub to use the X camera in the private plugin. The canonical `&format=map` polling URL and configuration settings remain unchanged. [Copy/paste guide](copy-paste.md).
