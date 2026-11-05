# Ship Spotlight design review and accepted text hierarchy

The UI design agent reviewed nine browser previews and all four templates against the pinned TRMNL 3.4.4 framework. The resulting renderer uses native typography, inverse paint, grid/flex, spacing and responsive auto/min/max widths. Custom code handles geographic projection/placement, glyphs and connectors.

## Ship annotation

The accepted reading order is ship name, unlabeled vessel type, flag/registry country, reported voyage (or destination alone), reported ETA when plausible, current reported speed, optional highlights, then ship details. Port names include countries when supported. Unknown origins/countries are omitted rather than turned into placeholder route stops.

“Good to know” uses sourced service-entry year, operator or class facts. Ship details put supported construction/shipyard country first, followed by length/width and other reported particulars. A service-entry year is never reused as a build year. Explicit construction years can accompany a build-country fact when actually available. Compact views retain the primary story and labeled dimensions; roomier views show the optional highlights and extra details.

## Port card and map credits

The port card reads “Port of Call,” a prominent port/country name, and “XX vessels recently reported near this port.” It contains no archive badge, report/fetch clock rows or source links. The count is distinct MMSIs with unexpired positions in the selected observation rectangle intersected with the reviewed harbor area. It is not a complete physical port census or a count of visible glyphs; source coverage, layout decluttering and the Spotlight annotation can hide vessels.

Source and license links share the native map attribution area with the complete OpenStreetMap credit. TRMNL explicitly preserves author-provided `.map__attribution` markup. Native flex wrapping accommodates compact views; its measured bounds are protected from cards, glyphs, labels and connectors.

Historical/state-test provenance remains in the preview page outside the device screen, in fixture metadata and screenshot documentation. The historical AIS coordinates and report times are unchanged. Production never loads these fixtures.

## Native design and connector

The ship surface uses native `inverse`, including its dark-mode reversal. Fixed black/white styling and the custom maximum-width override have been removed. Statistic captions and values use shared rows in roomier layouts; compact dimensions use explicitly labeled inline text. The Spotlight connector is three logical pixels wide with a seven-pixel separation halo, scaled with the native UI scale. Ordinary vessel-name leaders retain their weight. No route-like arrows are drawn on the map.

## Validation

The suite covers all layouts, OG/X/portrait, normal and one-bit dark modes, native multi-instance mashups, absent facts and documented state/synthetic fixtures. Checks include readable native text, correct fact order, omission of unavailable facts, construction/service-date distinction, inverse contrast, aligned dimensions, connector width/attachment, complete attribution and geographically exact marker positions. These are browser previews rather than physical-device validation.
