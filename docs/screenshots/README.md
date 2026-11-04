# Rendered previews

These PNGs are **Chromium browser previews**, not physical-device photos or hosted TRMNL screenshots. They use the pinned official TRMNL 3.4.4 runtime, MapLibre 5.24.0 and actual `maps.trmnl.com` vector tiles. Capture waits for native map readiness and `TRMNL_PLUGINS_READY`, fonts and attribution; a regression assertion keeps hulls above the native dither canvas.

The three Finnish fixtures are **genuine historical AIS captured on 4 November 2026, 17:07:02 UTC / 18:07:02 Europe/Berlin**. Screens label them ARCHIVE. Preserve that provenance when sharing; they are not current traffic. The "reported" counts include reports in the selected area; decluttering is separately disclosed. Standard/Closer use smaller extents than these Wider capture fixtures.

| Preview | Purpose |
|---|---|
| [OG Helsinki](og-helsinki.png), [Turku](og-turku.png), [Rauma](og-rauma.png) | Genuine historical full-screen reports, 800×480 |
| [Half-horizontal](og-half-horizontal.png), [half-vertical](og-half-vertical.png), [quadrant](og-quadrant.png) | Genuine historical compact layouts |
| [X landscape](x-landscape.png), [X portrait](x-portrait.png) | 1872×1404 and 1404×1872, 4-bit framework mode |
| [X half-horizontal](x-half-horizontal.png), [half-vertical](x-half-vertical.png), [quadrant](x-quadrant.png) | Genuine historical compact X layouts |
| [Dark](og-dark.png), [1-bit](og-one-bit.png) | Dark and 1-bit glyph/map contrast |
| [Empty](og-empty.png), [stale](og-stale.png), [unavailable](og-unavailable.png), [warming](og-warming.png) | Explicit STATE TEST fixtures, not observed incidents |
| [Map error](og-map-error.png) | Deliberately blocked native tile requests; diagnostic fallback |
| [Density](og-demo-density.png) | Explicitly synthetic DEMO positions, **not genuine maritime activity** |

The X preview applies the requested panel dimensions and a 2× UI scale rather than depending on a changing device alias. The ordinary OG preview requests 2-bit; `og-one-bit` exercises a 1-bit screen. Framework CSS/device paint chooses e-ink colors; no claim is made that these PNGs were produced by TRMNL's hosted image processor. Inspect on hardware before release. `results.json` and `results-additional.json` record the browser assertions for 19 distinct scenarios; it is generated only after all cases complete.

The official code assets were fetched from the pinned Git commit because direct canonical asset requests returned 403 in this cloud. Tiles themselves were genuinely requested at render time through the environment's TLS-verifying proxy relay. There are no hand-drawn shorelines or embedded raster base maps.
