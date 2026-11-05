# Rendered previews

These PNGs are **Chromium browser previews**, not physical-device photos or hosted TRMNL screenshots. They use the pinned official TRMNL 3.4.4 runtime, MapLibre 5.24.0 and actual `maps.trmnl.com` vector tiles. Capture waits for native map readiness and `TRMNL_PLUGINS_READY`, fonts and attribution; pixel checks reject blank screenshots, and geometry checks keep hulls above the native dither canvas and compare their final pixel positions against the map projection. Text boxes, names and leader lines are checked against actual rendered glyphs and attribution.

The three Finnish fixtures are **genuine historical AIS captured on 4 November 2026, 17:07:02 UTC / 18:07:02 Europe/Berlin**. The preview page identifies them as historical outside the device screen; fixture metadata and this documentation retain the dates. Preserve that provenance when sharing; they are not current traffic. The vessel counts include recent observations in the selected area; decluttering and annotation occlusion can reduce the visible glyph count without changing the recent-report count. Standard/Closer use smaller extents than these Wider capture fixtures.

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
| [Full](spotlight-full.png) | Independent harbor card plus connected PLYCA annotation, reported Hanko → Tilbury, grey context vessels |
| [Half-horizontal](spotlight-half-horizontal.png), [half-vertical](spotlight-half-vertical.png), [quadrant](spotlight-quadrant.png) | Two independent overlays, a mandatory connector and a geographically exact highlighted ship |
| [X](spotlight-x.png), [portrait](spotlight-portrait.png) | Large-screen native layout adaptations |
| [One-bit](spotlight-one-bit.png), [dark](spotlight-dark.png) | Size/fill/outline distinction without color dependence |
| [Four-quadrant mashup](spotlight-mashup-quadrants.png), [two-half mashup](spotlight-mashup-halves.png) | Independent map instances with highlighted subject and featured name |
| [Long-name layout test](spotlight-layout-test.png) | **Synthetic name/destination text on archived real positions**, explicitly marked STATE TEST; tests abbreviation and card clipping |
| [Selection fallback](spotlight-fallback.png) | **Artificial selection state on archived real positions**, explicitly marked STATE TEST; ordinary harbor overview when no subject qualifies |

Ordinary names are Off for the genuine Spotlight cases: the featured name remains visible in its extended annotation. Geometry checks require both its marker and label, and compare the marker with the map's actual projection to within one pixel. Full sweeps cover 36 individual views/states and four native mashups (12 independent map instances). Long annotation text uses native clamping; the underlying data retains the complete subject name. Context ships may be covered by the annotation, while the selected ship, harbor key and map credit remain clear. Native map camera framing moves the viewport, never the vessel coordinates.

The extended-label revision checks that the headline and at least three text rows are actually visible after native clamping, not merely that an empty card has valid bounds. It also checks the connector endpoint, separation of the harbor and ship overlays, permitted context occlusion and unchanged geographic projection. Plain harbor views use the same simplified port/country inset and map-level source credits. The annotation content is a provisional shortlist from the [ranked review](../ship-spotlight-content.md).

## Country-aware inverted annotation

The current Spotlight images use native inverse paint (adapting to dark mode), category labels, country-qualified ports and no position-time line in the ship annotation. Full and vertical-half views include supported country/flag references and plausible reported ETA; compact views show fewer fields. Original archived AIS positions/timestamps remain unchanged. Later country reference retrieval is dated separately in each fixture's `reference_enriched_at`. The browser checks verify native inverse contrast and the actual Spotlight connector width, UTC ETA filtering is covered by backend tests, and the horizontal compact case must retain context vessels in addition to its black subject.

## Native typography and connector follow-up

The ship annotation now uses native title and small-label roles, auto width with native responsive bounds, and inline labeled dimensions. The port card shows port/country and a scoped recent-vessel count; source/clock rows have been removed. The Spotlight identification line is three logical pixels wide with a seven-pixel halo; ordinary label leaders remain thin. Metadata size consistency, bottom-left corner anchoring and native inverse contrast are checked after the actual font/clamping pass.

The [dark Spotlight](spotlight-dark.png) case explicitly toggles dark mode. [Dark one-bit Spotlight](spotlight-one-bit-dark.png) is an additional case for the framework's separate one-bit inverse rules. These may display a light selected surface in dark mode, as intended. The previous fixed black/white override is removed. The sweep totals **40 scenarios: 36 individual views/states and four native mashups**.

## Current copy and source placement

The ship order is name → type → flag → voyage/ETA → current speed → sourced highlights → ship details. The port card contains Port of Call, port/country and a recent vessel-report count. Fintraffic/source and license links sit next to OpenStreetMap on the map, using the framework's supported author-provided attribution markup and native wrapping. Optional Wikidata/CC0 credit is in About/settings. A native flex row docks the port card four logical pixels from the map bottom-left edge and lets credits wrap beside it. All metadata uses one native small-label size, with bold labels and a larger ship name. Repeated “reported” qualifiers and draught are absent from the displayed copy. There are no archive/report/fetch rows in the product cards.

The screenshots remain historical captures on the dates above. Their preview page carries a provenance banner outside the device screen, and the fixture files retain original `snapshot_at`/`reported_at` plus later reference-retrieval dates. When sharing PNGs, keep this historical caption. State-test and synthetic-name images remain tests, not observed incidents or current activity.

## Outlined name/voyage badges

[Overview](labels-overview.png), [dark overview](labels-overview-dark.png), [Spotlight](labels-spotlight.png), [dark Spotlight](labels-spotlight-dark.png), [horizontal half](labels-spotlight-half-horizontal.png) and [quadrant](labels-spotlight-quadrant.png) explicitly enable the ship-label toggle. The reference is the supplied aircraft-tracking screen: compact outlined badges with a strong name and secondary voyage row. The theme uses native TRMNL canvas/outline/text roles. Context labels remain separate from the inverse Spotlight annotation.

The six added cases use the existing genuine 5 November 2026 archive. Optional voyage strings were recovered only from matching archived MMSI/report-time/position records and existing cached references; observation timestamps and coordinates were not changed. `rauma-labels.json` removes Spotlight for an overview presentation of the same observation scope. The original Spotlight images still test labels Off; Spotlight mashups now test labels On. Compact views may omit every ordinary badge when no safe space fits. Full overview/Spotlight cases require visible voyage badges, and every case checks actual label content and theme paint alongside geometry. The suite totals 40 scenarios, with the same twelve independent map instances across its four mashups.
