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

The [dark Spotlight](spotlight-dark.png) case explicitly toggles dark mode. [Dark one-bit Spotlight](spotlight-one-bit-dark.png) is an additional case for the framework's separate one-bit inverse rules. These may display a light selected surface in dark mode, as intended. The previous fixed black/white override is removed. The sweep totals **46 scenarios: 42 individual views/states and four native mashups**.

## Current copy and source placement

The ship order is name → type → flag → voyage/ETA → current speed → sourced highlights → ship details. The port card contains Port of Call, port/country and a recent vessel-report count. Fintraffic/source and license links sit next to OpenStreetMap on the map, using the framework's supported author-provided attribution markup and native wrapping. Optional Wikidata/CC0 credit is in About/settings. A native flex row docks the port card four logical pixels from the map bottom-left edge and lets credits wrap beside it. All metadata uses one native small-label size, with bold labels and a larger ship name. Repeated “reported” qualifiers and draught are absent from the displayed copy. There are no archive/report/fetch rows in the product cards.

The screenshots remain historical captures on the dates above. Their preview page carries a provenance banner outside the device screen, and the fixture files retain original `snapshot_at`/`reported_at` plus later reference-retrieval dates. When sharing PNGs, keep this historical caption. State-test and synthetic-name images remain tests, not observed incidents or current activity.

## Outlined name/voyage badges

[Overview](labels-overview.png), [dark overview](labels-overview-dark.png), [Spotlight](labels-spotlight.png), [dark Spotlight](labels-spotlight-dark.png), [horizontal half](labels-spotlight-half-horizontal.png) and [quadrant](labels-spotlight-quadrant.png) explicitly enable the ship-label toggle. The reference is the supplied aircraft-tracking screen: compact outlined badges with a strong name and secondary voyage row. The theme uses native TRMNL canvas/outline/text roles. Context labels remain separate from the inverse Spotlight annotation.

The six added cases use the existing genuine 5 November 2026 archive. Optional voyage strings were recovered only from matching archived MMSI/report-time/position records and existing cached references; observation timestamps and coordinates were not changed. `rauma-labels.json` removes Spotlight for an overview presentation of the same observation scope. The original Spotlight images still test labels Off; Spotlight mashups now test labels On. Compact views may omit every ordinary badge when no safe space fits. Full overview/Spotlight cases require visible voyage badges, and every case checks actual label content and theme paint alongside geometry. The suite totals 46 scenarios, with the same twelve independent map instances across its four mashups.

## Port facts and compact credits

Six additional cases enable **Show port facts?**: [full overview](facts-full.png), [dark full Spotlight](facts-full-dark.png), [half vertical](facts-half-vertical.png), [OG quadrant](facts-quadrant.png), [X quadrant](facts-x-quadrant.png) and [portrait](facts-portrait.png). The OG quadrant deliberately hides the optional blurb; X shows it. Geometry checks ensure the card stays bottom-left and credits remain inline with a transparent wrapper, alongside label/leader clearance. All fixtures retain their original vessel positions and timestamps. `LVMRX` is rendered as Mērsrags and FAIRWAY WORKS as an activity; neither changes source data.


## Optional vessel legend

**Show map legend** is off by default. On full-screen maps it adds a compact inline key above the source credits, beside the harbor card: Cargo/tanker, Passenger, Fishing, Other, and Unknown. Each small icon sits beside its label. The large outlined panel has been removed; native canvas backgrounds hug each individual entry. The key uses the same JavaScript shape dictionary as the markers; Other covers the broad AIS category including service vessels and leisure craft. Native flex, spacing, icon dimensions and small-label roles handle its appearance and wrapping. It is omitted from half and quadrant layouts.

[Overview](legend-overview.png), [Spotlight](legend-spotlight.png), [dark](legend-dark.png), [one-bit](legend-one-bit.png), [X landscape](legend-x.png), [X portrait](legend-portrait.png), and [OG portrait](legend-og-portrait.png) use the unchanged genuine archived AIS fixtures from 5 November 2026. The [Seattle one-bit](legend-seattle.png) and [Seattle X](legend-seattle-x.png) cases use the actual polling endpoint response captured on 11 November 2026 at 22:37 CET, retained in [seattle-legend.json](../../fixtures/seattle-legend.json). These are historical browser previews, not current traffic. All nine enable port facts and ship labels to check clearance under a fuller layout. The geometry checks reserve the legend against ship markers, labels, Spotlight and connector lines, verify five distinct paths, preserve the bottom-left harbor card, and reject overflow or overlapping credits. Additional checks reject a large framed key and ensure the legend/credits dock to the bottom when beside the port card; narrow portrait screens may wrap them immediately above it. Results are recorded in [results-legend.json](results-legend.json).


## Counts, labels and landmarks · 11 November 2026

The refreshed individual-view sweep contains 56 scenarios, plus four native mashups (twelve independent map instances). Each checks the drawn-vessel count against **on map**, full voyage text or a semantically shortened version, route overflow, and landmark clearance. Landmarks are current CC0 reference context added to historical observations; no vessel observation or timestamp in the original captures is changed. Their [coordinate sources](../landmark-sources.json) are separate from the AIS capture dates. Native type sizes and fixed harbor framing remain in use.

`PLAYWRIGHT_EXECUTABLE_PATH=/usr/bin/chromium MAP_RELAY=true node scripts/check-trail.mjs` performs an additional synthetic DOM-only trail geometry test. It inserts invented points solely in a disposable browser document, checks exact projection of two segments, saves no image, and never modifies or publishes an AIS fixture. Backend tests separately verify storage parity, original timestamps, bounded sampling, checkpoint restoration, expiry, and rejection of jumps and out-of-order fixes.


[Observed Spotlight trail](observed-trail.png) shows NEUENFELDE in Hamburg from an actual deployed API response at **23:41:40 CET, 11 November 2026**. [The retained response](../../fixtures/observed-trail.json) includes three original AIS fixes, at 23:37:16, 23:41:07 and 23:41:16 CET. Coordinates and timestamps are unchanged. The screenshot is an archived browser preview, not current traffic or a device photograph. It explicitly requires at least one visible trail segment, alongside count, label, landmark and source-clearance checks.


## Count wrapping and landmark pins · 12 November 2026

The count is a single text run inside its native label. The earlier nested suffix became a separate flex item because TRMNL labels use `inline-flex`; leading whitespace collapsed at that boundary, and the suffix could shrink into several short lines. The complete count now has an explicit space before the divider, with non-breaking spaces keeping the divider and “N on map” together. Native typography is unchanged. Browser checks measure the rendered suffix fragments and the visible gap before the divider, beyond checking the text value and overflow. Four additional [OG portrait half](count-og-portrait-half.png), [OG portrait quadrant](count-og-portrait-quadrant.png), [X portrait half](count-x-portrait-half.png), and [X portrait quadrant](count-x-portrait-quadrant.png) cases use the existing genuine archived Seattle capture. No observation timestamps or coordinates are changed.

Landmarks now use a small hollow map pin with an ink centre, a native canvas fill and a separation halo. The pin's tip is the source coordinate; its larger footprint is reserved during placement. Light/dark and bit-depth previews exercise the same icon. Geometry checks compare each pin tip with MapLibre's projection of its source coordinate.

## 80-candidate comparison · 12 November 2026

Twenty additional panels compare 40 and 80 candidates from the **same genuine archived Seattle capture**, with unchanged source timestamps and camera settings. They cover every layout, X landscape/portrait, Spotlight and dark mode. The overview was captured at **09:19:04 CET**, and Spotlight separately at **09:19:41 CET**, on 12 November. These are historical browser previews, not current traffic. [Comparison, exact provenance and results](../map-candidates.md) · [OG after](candidates-og-80.png) · [X after](candidates-x-80.png) · [Spotlight after](candidates-spotlight-80.png). X comparison exports use the native framework scale once, at the panel's 1872×1404 or portrait 1404×1872 dimensions.

## Facts and related POIs · 12 November 2026

Fifteen additional **POI reference scenarios** select a reviewed static fact alongside genuine archived AIS. They do not claim that the fact was selected at the capture's historical hour. Vessel positions, report timestamps and the source camera are unchanged. [Full review and exact capture provenance](../port-fact-pois.md) · [Results](results-poi-facts.json).

[Ballard Locks](poi-seattle-locks.png), [Space Needle](poi-seattle-needle.png), [dark mode](poi-seattle-dark.png), [Spotlight](poi-seattle-spotlight.png), [Elbphilharmonie](poi-hamburg-hall.png) and [Forum Marinum](poi-turku-museum.png) demonstrate related labels getting space before ship names. Other cases explicitly exercise crowded source pins, clipping, small layouts and facts switched off. Diagnostics retain whether each related pin is in frame and which actual hulls block it. Omission in those cases preserves the fixed map and the higher priority of vessel hulls. The regular 56-view regression sweep also passes with the expanded static reference context.
