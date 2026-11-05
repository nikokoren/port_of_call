# Free sources for enriching Port of Call

**Product decision, 4 November 2026: free data sources only.** No paid subscriptions, purchased API credits, paid upgrades or trials that become paid. The community recipe must not require users to buy a data account. A limited free tier is usable only when requests can be hard-capped with no automatic charges and the feature degrades cleanly when that allowance is exhausted.

Free access must also permit the recipe's reuse. Prefer public domain, CC0 or attribution-compatible open data. Publicly visible pages and free browser accounts are not permission to scrape or redistribute them.

## Sources in scope

| Source | Useful additions | Access / reuse | Role |
|---|---|---|---|
| **AISStream, already connected** | Reported destination/ETA, dimensions, draught, IMO/call sign and navigation status alongside current position | Existing free shared stream; the public-display/cache review documented in the data evaluation still applies | First priority: retain and validate useful fields already received, with separate voyage-field timestamps. No additional paid feed or per-user connection. |
| **Wikidata** | Ship class, builder, operator, service dates, some dimensions, port identifiers and coordinates | Public API; structured data CC0 | Optional background facts and a reviewed destination/port alias catalog. Match ships by IMO. Missing coverage must not prevent a ship being featured. |
| **Digitraffic / Portnet** | Previous/next ports and planned/actual arrival/departure times | Free API; CC BY 4.0 with attribution | Regional enrichment for Finnish calls. Use only a relevant dated record; an old Finnish call does not establish the origin of a ship's current voyage elsewhere. |
| **NOAA CO-OPS** | US harbor water levels, tide predictions and station observations | Public API; no key needed for the tested request | Optional harbor context. Keep observation/prediction, datum, units and timestamps clear; do not calculate safe passage/clearance from tide plus AIS draught. |
| **Wikimedia Commons** | Photos of some identified ships | Individual-file licenses; no universal image license | Optional, with public-domain/CC0 images preferred initially. Otherwise satisfy the exact file's license/attribution requirements. Original generic ship-type silhouettes remain the simpler fallback. |

## Ship Spotlight under the free-only constraint

The core card should work with a genuine current position, a usable name and available AIS facts. Reported destination, reported ETA, type, dimensions and speed can provide a useful subject without a commercial history service. Wikidata adds optional context when an exact identifier match exists.

**A previous/departure port is not a standard AIS field.** Show it only when a suitable free official record actually supports that claim. Otherwise omit the field or show it as unknown. Our own future bounded observation history could support **Previously seen near [harbor]**, with its observation date; that is not a confirmed departure or port call.

Do not make complete From → To information a requirement for selection, and do not invent origin from heading, flag or old destination text. A globally complete previous-port feature is not promised under the current free-source coverage. The feature remains useful when origin is unknown.

## Verified source details

Research retrieved on 4 November 2026. No paid account was created or activated.

### Existing AIS fields

AISStream's official schema includes `ShipStaticData.Destination`, `Eta`, `Dimension`, `MaximumStaticDraught`, `ImoNumber`, `CallSign`, and dynamic navigation status. The Spotlight normalization now retains and validates those fields with independent freshness timestamps; no additional subscription is needed. [Implementation](ship-spotlight.md).

Schema: https://github.com/aisstream/ais-message-models/blob/291c17682a1108f722c130402089678156613320/type-definition.yaml

### Wikidata and image references

- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.wikidata.org/w/api.php
- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia

The API verified `P458` = IMO ship number, `P587` = MMSI, `P1937` = UN/LOCODE and `P625` = coordinate location. Structured Wikidata is CC0. A reviewed subset can provide port coordinates/codes and aliases without assuming that every transport location is a seaport.

An illustrative Queen Mary 2 (`Q191888`) lookup returned identifiers, length, service-entry date, builder/operator references and an image reference. This demonstrates notable-vessel metadata, not current presence in a selected harbor. The linked Commons image was **CC BY-SA 4.0, attribution required**, which proves that CC0 entity data does not grant a blanket image license. Do not relabel inception/launch/service-entry dates as a build year without confirming their meaning.

### Free Finnish port calls

- https://www.digitraffic.fi/en/marine-traffic/
- https://meri.digitraffic.fi/api/port-call/v1/port-calls
- https://www.digitraffic.fi/en/terms-of-service

A gzip-enabled request returned HTTP 200 and **259 port-call records** at research time. Fields included `prevPort`, `nextPort`, `portToVisit`, `imoLloyds`, `mmsi`, and area details containing `eta`, `ata`, `etd`, `atd`, their source/timestamp fields and reported draught. Fields can be empty, reported or planned; their presence alone does not establish an actual event.

Fintraffic's terms explicitly permit distribution/adaptation, including commercial use, under CC BY 4.0 with attribution, links and modification notice. Retain only the relevant ship/voyage fields, not unrelated master, agent or administrative details. Coverage concerns Finnish calls rather than a complete global history.

### Harbor context

https://api.tidesandcurrents.noaa.gov/api/prod/

A keyless NOAA water-level request for station `9410660` returned HTTP 200, identified Los Angeles and supplied timestamped metric data relative to MLLW. Water-level observations and tide predictions are separate products. This is optional context, not a navigation capability or a global tide source.

## Sources not selected

**VesselFinder, MarineTraffic/Kpler, Datalastic, Searoutes and paid API.SH plans are excluded by the free-only decision.** Earlier research into their fields or prices is not an implementation recommendation. No paid-provider trial, quote or credit purchase is a prerequisite or fallback for this feature. API.SH's limited free allowance is also not a planned dependency: reuse rights for its third-party content were not established, and allowance exhaustion must not lead to an upgrade requirement.

**Equasis** is suitable for human research but its accessible conditions forbid bulk downloads and commercial reproduction. Do not scrape it to obtain otherwise unavailable free metadata.

**Full UN/LOCODE imports need clarification.** The official site's generic terms allow personal non-commercial copying without redistribution/derivatives, while its footer says UN/CEFACT standards are under CC BY 4.0. The dataset's scope is not explicit enough here to call it cleared. The DataHub/GitHub wrapper expressly says its PDDL applies only to the maintainers' own work, not the underlying list. NGA's World Port Index is a further reference candidate, but its page returned HTTP 503 and current download/reuse details were not verified. Start with reviewed CC0 Wikidata port records instead.

References: https://unlocode.unece.org/terms · https://github.com/datasets/un-locode · https://msi.nga.mil/Publications/WPI · https://www.equasis.org/

## Delivery order

1. Retain and validate the additional AIS fields already received; measure completeness on real reports.
2. Add optional CC0 facts and reviewed destination aliases, with bounded shared caching and no charges.
3. Add free official port-call facts only where relevant; keep origin unknown elsewhere.
4. Make selection favor fresh, informative, distinctive and varied vessels without requiring origin, a photo or an external metadata match.
5. Add optional images/context only when useful and freely reusable. Missing or rate-limited enrichment should omit a fact rather than block the map or trigger a paid fallback.

Hosting is a separate deployment question: no paid host has been approved or provisioned. Existing infrastructure or a verified sustainable free service should be assessed for the persistent collector; brief cron samples are not a replacement for continuous AIS collection. Free data does not by itself prove zero operating cost, and no such promise is made here.

## Implementation evidence · 5 November 2026

Ship Spotlight now uses the existing AIS fields plus optional exact-IMO Wikidata reference facts and relevant current Finnish Portnet calls. Genuine Finnish captures found 54/54, 24/25 and 17/18 suitable observations in Helsinki, Turku and Rauma, with source-specific field counts in `fixtures/spotlight-metrics.json`. A subsequent two-minute live AISStream follow-up observed 833 current per-area observations and 93 eligible subjects in ten areas; three covered areas had positions but insufficient static facts during this short cold start. See [aggregate evidence](coverage/README.md#spotlight-field-follow-up--5-november-2026).

AIS ETA is retained without inventing a year. Digitraffic's draught is converted from decimetres; AISStream's floating-point draught is decoded metres, consistent with the upstream AIS decoder's `Field10` conversion (https://github.com/BertoldVdb/go-ais/blob/master/messages.go and https://github.com/BertoldVdb/go-ais/blob/master/codec.go). Saturated draught/dimension values are omitted rather than treated as exact measurements. Optional ship images and NOAA context remain future enhancements, not dependencies of this implementation.

The accepted country/ETA follow-up uses additional CC0 Wikidata statements: P2979 (maritime identification digits), P297 (ISO country code), P8047 (ship registry country), P1071 (creation site), P176 (builder) and P17 (country), with qualified-current-reference checks. No external MID database, paid registry or extra package is required. Relevant Finnish Portnet records additionally retain their reported nationality code. Country/flag inference and yard-country limits are explicit in [Ship Spotlight](ship-spotlight.md). The raw AIS ETA remains unchanged alongside a separately marked inferred-year estimate.
