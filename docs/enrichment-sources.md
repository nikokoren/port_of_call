# Sources for enriching Port of Call

Research checked 4 November 2026. These sources supplement the proven AISStream position feed; there is no reason to buy another global position feed just to add ship facts. Paid services below were evaluated from their public documentation/terms, not through purchased API access. No account was created and no paid service was activated.

## Recommended shortlist

| Source | What it adds | Cost/access | Reuse and coverage considerations |
|---|---|---|---|
| **Wikidata** | Ship class, builder, operator, service dates, dimensions and image references where populated; port identifiers/coordinates | Public API; structured data CC0 | Strong inexpensive background enrichment, particularly for notable ships. Ordinary merchant vessels and small craft can be missing. Match by IMO, with MMSI as an additional identifier; preserve statement dates/qualifiers. Image references do not grant image rights. |
| **VesselFinder Voyage + Master** | Last recorded port/country/departure time; flag, build year, builder, dimensions, GT/NT/DWT, TEU and other capacity, owner/manager | Credit-based API; commercial terms | Best first commercial candidate to evaluate for Ship Spotlight's missing previous-port field. Standard terms do **not** authorize a public community recipe: get written permission covering third-party display, caching/retention and derived screens. Test coverage on our selected vessels before buying a larger plan. |
| **MarineTraffic / Kpler** | Single-vessel port-call history, arrivals/departures, richer vessel particulars; broader maritime intelligence products | Commercial API; scope/pricing by agreement | Useful alternative for history/registry needs. Some documented particulars endpoints are legacy and point to newer Kpler APIs. Require a quote for the actual fields, coverage and public-display/cache rights, rather than assuming a web subscription grants API redistribution. |
| **Digitraffic / Portnet** | Previous/next port fields and planned/actual arrival/departure times, linked to IMO/MMSI | Public API; CC BY 4.0 with attribution | Useful for Finnish calls and our Finnish profile, not a complete global port-call history. Its records can refer to foreign previous/next ports, but that does not establish worldwide coverage. Keep planned, actual and reported values distinct. |
| **Port gazetteer** | Convert reported destination codes/aliases into a named port, country and map coordinate | Wikidata offers CC0 records; UN/LOCODE and NGA World Port Index are further reference candidates | Essential for destination resolution. UN/LOCODE also covers airports/other transport locations, so filter/review ports and avoid ambiguous matches. Do not assume a wrapper's PDDL/software license grants rights to the underlying UN/LOCODE list. See the primary-term conflict below. |
| **Wikimedia Commons** | Photographs of some identified ships | Public API; individual-file licenses | Optional visual enrichment. Fetch author/license/attribution metadata for each file; many images require attribution and ShareAlike. An image linked from CC0 Wikidata is not itself necessarily CC0. Generic, clearly labeled ship-type silhouettes remain a simpler option. |
| **NOAA CO-OPS** | US harbor water levels, tide predictions and station observations | Public API; no key needed for tested request | Context for the six US areas, rather than vessel identity/history. Show observation/prediction, units, datum, station and timestamp accurately. Do not infer safe passage/clearance from tide plus AIS draught. |

## What was verified

### VesselFinder: particularly relevant to the missing “From” field

Official docs:
- https://api.vesselfinder.com/docs/
- https://api.vesselfinder.com/docs/response-voyage.html
- https://api.vesselfinder.com/docs/response-master.html
- https://api.vesselfinder.com/docs/vessels.html
- https://api.vesselfinder.com/docs/portcalls.html
- https://api.vesselfinder.com/docs/openapi.yaml
- https://www.vesselfinder.com/terms

The Voyage dataset explicitly lists `LOCODE`, `LASTPORT`, `LASTCOUNTRY` and `DEPARTURE`. Master includes flag state, year built, shipbuilder, registered owner/manager, classification society, dimensions, draught, GT/NT/DWT and container/gas/crude capacity.

The documented `Vessels` method returns AIS by default (1 credit/returned vessel), with optional Voyage (+1) and Master (+2). MasterData separately costs 3 credits/record. These are credits per returned record, not necessarily per HTTP request. No verified currency conversion or public-display license quote was obtained, so no monthly dollar price is claimed.

The current standard terms define permitted purpose as personal informational or internal organizational use. They prohibit publishing/redistributing/sublicensing content to third parties, and caching beyond agreed retention, unless expressly permitted in writing. A small credit purchase alone therefore does not clear our public recipe. A suitable written agreement could make this source useful; it should explicitly cover cached facts rendered on TRMNL devices and any fields exposed by our polling JSON endpoint. A display-only grant must not be assumed to permit an open raw-data API.

A provider's last *recorded* port is not automatically the origin of an entire voyage or an official port declaration. Preserve the source/event/departure timestamp and handle missing calls. Avoid labeling the current port or a stale last-call record as a newly verified departure elsewhere.

### MarineTraffic / Kpler

https://servicedocs.marinetraffic.com/ was accessible, including its embedded API specification. It documents a single-vessel port-calls service returning arrival/departure information over a period, and a port-oriented calls service. Its old Vessel Particulars endpoint is explicitly marked legacy and links to a new Kpler version. Commercial API access and redisplay rights were not tested or purchased.

### Digitraffic / Portnet: a real free enrichment response

- https://www.digitraffic.fi/en/marine-traffic/
- https://meri.digitraffic.fi/api/port-call/v1/port-calls
- https://www.digitraffic.fi/en/terms-of-service

A gzip-enabled request returned HTTP 200 and **259 port-call records** at research time. Fields included `prevPort`, `nextPort`, `portToVisit`, `imoLloyds`, `mmsi`, vessel name, and area details containing `eta`, `ata`, `etd`, `atd`, their source/timestamp fields and reported draught. Presence of a field does not establish that it is populated or an actual rather than expected event.

The terms explicitly allow distribution/adaptation, including commercial use, under CC BY 4.0 with attribution, links and modification notice. Keep only the voyage fields needed for the feature; the full response also exposes unrelated administrative/master/agent fields that the recipe does not need.

### Wikidata and Commons: different rights

- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.wikidata.org/w/api.php
- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia

The API verified `P458` = IMO ship number, `P587` = MMSI, `P1937` = UN/LOCODE and `P625` = coordinate location. Structured Wikidata is CC0.

An illustrative lookup of Queen Mary 2 (`Q191888`) returned an IMO identifier, MMSI, length, service-entry date, operator/builder references and an image reference. This demonstrates metadata availability for that notable vessel; it is **not a claim that the vessel was in one of our harbors**. The linked Commons image's API metadata reported **CC BY-SA 4.0, attribution required**. That is a concrete example of why CC0 entity data must not be treated as a blanket image license.

Do not turn an inception, launch, commission or service-entry date into “year built” without confirming the property's meaning. Resolve entities by identifiers, not a fuzzy ship-name match; ships are renamed and names are reused.

### Port directory caveat

- https://unlocode.unece.org/
- https://unlocode.unece.org/terms
- https://datahub.io/core/un-locode
- https://github.com/datasets/un-locode
- https://msi.nga.mil/Publications/WPI

The UN/LOCODE site's generic terms permit personal, non-commercial copying without redistribution/derivatives, while its footer says UN/CEFACT standards are free under CC BY 4.0. The scope for the code-list dataset itself is not explicit enough here to call it cleared. The DataHub/GitHub wrapper expressly says its PDDL applies only to the maintainers' scripts/layout, not the underlying list. Get clarification before mirroring that dataset into a public recipe.

NGA's World Port Index is a relevant harbor reference candidate, but its official page returned HTTP 503 during this check; current download/reuse details were not verified. A small reviewed CC0 Wikidata port/alias catalog is a clearer starting point while these sources are evaluated. A directory coordinate represents a port/location, not a berth or proof that a vessel called there.

### NOAA CO-OPS

Official docs: https://api.tidesandcurrents.noaa.gov/api/prod/

A keyless water-level request for station `9410660` returned HTTP 200 and identified the station as Los Angeles, with timestamped metric data relative to the requested MLLW datum. This verifies an optional contextual API, not a navigation/safety capability or global tide coverage. Water-level observations and tide predictions are different products.

## Secondary options and exclusions

**API.SH** currently documents a 1-credit vessel endpoint with last port/arrival, reported voyage fields, flag/name history and particulars, and a port endpoint with expected/recent calls. Its docs explicitly describe approximate whole-degree positions and subscriber-only fields returning null. Its terms say it retrieves publicly available third-party website information; no license clearing the underlying material for our public recipe was established. Treat it as a possible prototype comparison, not a substitute for precise AIS or a cleared official feed.

References: https://api.sh/docs/vessels-vessel · https://api.sh/docs/vessels-port · https://api.sh/legal/terms

**Datalastic** is another commercial enrichment/history candidate to benchmark, but its current API-reference and pricing pages returned HTTP 403 from this machine. No current endpoint-specific coverage, price or display rights were verified here. Do not quote remembered prices as current offers.

**Equasis** is useful for human vessel research, but its accessible conditions forbid bulk downloads and commercial reproduction. A free browser account is not an automated enrichment API license; do not scrape it for the recipe.

References: https://datalastic.com/api-reference/ · https://datalastic.com/pricing/ · https://www.equasis.org/

## Recommended order and budget model

1. **Retain the AIS fields already being received.** Destination, ETA, dimensions, draught, IMO/call sign and navigation status can add substantial value before buying another feed. Measure actual completeness and maintain independent voyage-field timestamps.
2. **Add optional CC0 background facts and a reviewed port gazetteer.** Match by IMO, cache identity facts for weeks, and leave unknown or ambiguous destinations unresolved.
3. **Trial one licensed port-call/history provider for featured ships only.** Start a commercial conversation with VesselFinder and compare Kpler if coverage/terms require it. Ask specifically for our 13 areas, selected-vessel use, cache retention, public community-recipe display and pricing per returned record.
4. **Add photos/context only where they improve the e-ink screen.** They need not block a good map-and-facts feature.

At one subject every three hours, 13 harbors imply about **104 selected-vessel lookups/day**, before early replacements and cache hits. Shared server caching prevents that workload multiplying with installed devices. A VesselFinder AIS+Voyage response would cost two documented credits per returned vessel; adding Master makes it four. Currency pricing and the right to display publicly must come from the actual agreement. For registry facts, a weeks-long cache can avoid repeated Master requests. Voyage/history facts need a shorter lifetime and their own timestamps.

The final choice should be made from real sample coverage and the public-display agreement, not just a provider's marketing field list or low per-call price. Keep source, observation/event time and confidence separate when merging data.
