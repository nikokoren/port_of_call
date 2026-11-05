# Rendered previews

These PNGs are **Chromium browser previews**, not physical-device photos or hosted TRMNL screenshots. They use the pinned official TRMNL 3.4.4 runtime, MapLibre 5.24.0 and actual `maps.trmnl.com` vector tiles. Capture waits for native map readiness and `TRMNL_PLUGINS_READY`, fonts and attribution; pixel checks reject blank screenshots, and geometry checks keep hulls above the native dither canvas and compare their final pixel positions against the map projection. Text boxes, names and leader lines are checked against actual rendered glyphs and attribution.

The three Finnish fixtures are **genuine historical AIS captured on 4 November 2026, 17:07:02 UTC / 18:07:02 Europe/Berlin**. Screens label them ARCHIVE. Preserve that provenance when sharing; they are not current traffic. The "reported" counts include reports in the selected area; decluttering is separately disclosed. Standard/Closer use smaller extents than these Wider capture fixtures.

| Preview | Purpose |
|---|---|
| [OG Helsinki](og-helsinki.png), [Turku](og-turku.png), [Rauma](og-rauma.png) | Genuine historical full-screen reports, 800×480 |
| [Half-horizontal](og-half-horizontal.png), [half-vertical](og-half-vertical.png), [quadrant](og-quadrant.png) | Genuine historical compact layouts |
| [X landscape](x-landscape.png), [X portrait](x-portrait.png) | 1872×1404 and 1404×1872, 4-bit framework mode |
| [X half-horizontal](x-half-horizontal.png), [half-vertical](x-half-vertical.png), [quadrant](x-quadrant.png) | Genuine historical compact X layouts |
| [OG four-quadrant mashup](og-mashup-quadrants.png), [X two-half mashup](x-mashup-halves.png) | Multiple independent recipe instances in native framework mashups |
| [Dark](og-dark.png), [1-bit](og-one-bit.png) | Dark and 1-bit glyph/map contrast |
| [Empty](og-empty.png), [stale](og-stale.png), [unavailable](og-unavailable.png), [warming](og-warming.png) | Explicit STATE TEST fixtures, not observed incidents |
| [Map error](og-map-error.png) | Deliberately blocked native tile requests; diagnostic fallback |
| [Density](og-demo-density.png) | Explicitly synthetic DEMO positions, **not genuine maritime activity** |

The X preview applies the requested panel dimensions and a 2× UI scale rather than depending on a changing device alias. The ordinary OG preview requests 2-bit; `og-one-bit` exercises a 1-bit screen. Framework CSS/device paint chooses e-ink colors; no claim is made that these PNGs were produced by TRMNL's hosted image processor. Inspect on hardware before release. `results.json` records the individual-view sweep and `results-mashups.json` records native multi-instance mashups; each is written only after its cases complete. The native attribution font can extend by one pixel per UI scale unit; the scroll check allows only that measured rounding. Card, label and marker bounds have separate strict checks.

The official code assets were fetched from the pinned Git commit because direct canonical asset requests returned 403 in this cloud. Tiles themselves were genuinely requested at render time through the environment's TLS-verifying proxy relay. There are no hand-drawn shorelines or embedded raster base maps.

## Updated layout

These renders use Downstream’s full-map layout, with a native outlined information box bottom left and an integer-zoom frame chosen to clear that box. Ship names use Hotspots’ adjacent/offset placement and leader lines, with fewer names in compact views. Both reference repositories are unchanged. Reports remain the same genuine historical captures, so changes in shown marker counts reflect framing/decluttering rather than new or invented traffic.

The preview host explicitly isolates the screen’s stacking context, matching the device wrapper’s transformed screen. Without it, X mashup views with native negative stacking could produce an all-white PNG despite valid DOM geometry. `tests/preview-pixels.test.mjs` reproduces that class of false pass and the render scripts now reject it.

## Ship Spotlight · 5 November 2026

The Spotlight captures use genuine AIS observations at **08:28 UTC / 09:28 Europe/Berlin** on 5 November 2026, with original field/report times and free CC0 Wikidata facts. PLYCA's reported Hanko origin comes from a relevant actual Rauma Portnet call (Fintraffic CC BY 4.0), not inferred motion. The other archived subjects retain unknown origin. These are historical test captures, not current traffic.

| Spotlight preview | Purpose |
|---|---|
| [Full](spotlight-full.png) | PLYCA, reported from Hanko / to Tilbury, available AIS and free reference facts |
| [Half-horizontal](spotlight-half-horizontal.png), [half-vertical](spotlight-half-vertical.png), [quadrant](spotlight-quadrant.png) | Fewer facts and a protected, geographically exact highlighted ship |
| [X](spotlight-x.png), [portrait](spotlight-portrait.png) | Large-screen native layout adaptations |
| [One-bit](spotlight-one-bit.png), [dark](spotlight-dark.png) | Size/fill/outline distinction without color dependence |
| [Four-quadrant mashup](spotlight-mashup-quadrants.png), [two-half mashup](spotlight-mashup-halves.png) | Independent map instances with highlighted subject and featured name |
| [Long-name layout test](spotlight-layout-test.png) | **Synthetic name/destination text on archived real positions**, explicitly marked STATE TEST; tests abbreviation and card clipping |
| [Selection fallback](spotlight-fallback.png) | **Artificial selection state on archived real positions**, explicitly marked STATE TEST; ordinary harbor overview when no subject qualifies |

Ordinary names are Off for the genuine Spotlight cases: the featured name remains visible. Geometry checks require both its marker and label, and compare the marker with the map's actual projection to within one pixel. Full sweeps cover 29 individual views/states and four native mashups (12 independent map instances). Long map labels may be abbreviated; the card/data retain the subject's name. Native map camera framing moves the viewport, never the vessel coordinates.
