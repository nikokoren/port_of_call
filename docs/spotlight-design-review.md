# Ship Spotlight design review and accepted text hierarchy

The UI design agent reviewed nine browser previews and all four templates against the pinned TRMNL 3.4.4 framework. The resulting renderer uses native typography, inverse paint, grid/flex, spacing and responsive auto/min/max widths. Custom code handles geographic projection/placement, glyphs and connectors.

## Ship annotation

The accepted reading order is ship name, unlabeled vessel type, flag/registry country, voyage (or destination alone), ETA when plausible, current speed, optional highlights, then ship details. Port names include countries when supported. Unknown origins/countries are omitted rather than turned into placeholder route stops.

“Good to know” uses sourced service-entry year, operator or class facts. Ship details put supported construction/shipyard country first, followed by length/width. A service-entry year is never reused as a build year. Explicit construction years can accompany a build-country fact when actually available. Compact views retain the primary story and labeled dimensions; roomier views show the optional highlights and extra details.

## Port card and map credits

The port card reads “Port of Call,” a prominent port/country name, and “XX vessels seen near this port.” It contains no archive badge, report/fetch clock rows or source links. The count is distinct MMSIs with unexpired positions in the selected observation rectangle intersected with the reviewed harbor area. It is not a complete physical port census or a count of visible glyphs; source coverage, layout decluttering and the Spotlight annotation can hide vessels.

Fintraffic/source and license links share the native map attribution area with the complete OpenStreetMap credit. Optional Wikidata/CC0 credit is in the plugin About/settings description, in both provider packages. TRMNL explicitly preserves author-provided `.map__attribution` markup. Native flex wrapping accommodates compact views; its measured bounds are protected from cards, glyphs, labels and connectors.

Historical/state-test provenance remains in the preview page outside the device screen, in fixture metadata and screenshot documentation. The historical AIS coordinates and report times are unchanged. Production never loads these fixtures.

## Native design and connector

The ship surface uses native `inverse`, including its dark-mode reversal. Fixed black/white styling and the custom maximum-width override have been removed. All Spotlight metadata uses the same native small-label font and size, with bold field/section labels and a larger ship-name title. Dimensions use labeled inline text in every layout. Draught is omitted entirely from the Spotlight card and its presentation data. The port card and map attribution occupy a native flex row anchored four logical pixels from the map edges; credits wrap in the space beside the card instead of pushing it upward. The Spotlight connector is three logical pixels wide with a seven-pixel separation halo, scaled with the native UI scale. Ordinary vessel-name leaders retain their weight. No route-like arrows are drawn on the map.

## Validation

The suite covers all layouts, OG/X/portrait, normal and one-bit dark modes, native multi-instance mashups, absent facts and documented state/synthetic fixtures. Checks include readable native text, correct fact order, omission of unavailable facts, construction/service-date distinction, inverse contrast, consistent metadata type size and corner anchoring, connector width/attachment, complete attribution and geographically exact marker positions. These are browser previews rather than physical-device validation.
