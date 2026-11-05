# Roadmap

**Product constraint: free data sources only.** No paid subscriptions, API credits, paid upgrades or expiring trials as feature dependencies. Optional enrichment must fail gracefully without a payment requirement.

V1 ships a map of recently reported positions. First stabilize Finnish operation with private TRMNL tests and multi-day monitoring. Extend the harbor registry only with provider coverage and license evidence; subscription quotas are an operator concern, never a setting for recipe users.

## Next · Major harbors

Prepare the [15-area collection](major-ports.md), weighted toward the US and Europe. The catalog, one-subscription coverage probe and matching-form packager are implemented. A genuine 15-minute run data-verified 13 areas; two Asian areas remain excluded after no reports. Public release still needs deployment and public-display/cache rights confirmation, plus longer reliability monitoring. The Finnish profile stays available; neither a successful subscription nor a free key automatically promotes a candidate.

## V2 · Arrivals & Departures

Add a licensed official port-call/schedule provider through a separate adapter and versioned `/api/v1/harbors/{id}/port-calls` contract. Use Digitraffic Portnet/NEMO for Finland and evaluate freely reusable official port APIs elsewhere. Verify ship-name completeness, rate limits, timestamp semantics and redistribution rights. Paid API.SH, Searoutes, VesselFinder and other commercial feeds are excluded; a board may remain regional when no suitable free schedule source exists. No API.SH approximate positions should drive map markers.

Keep expected/actual time, timezone, event type and source status separate. Mark unknown explicitly. A position inside a rectangle cannot establish a berth, authoritative arrival, departure, delay or ETA. Do not turn AIS destination text into a schedule. Add the `board` display setting only when a genuine schedule layout and its tests work in all sizes.

## Ship Spotlight · Implemented

The optional **Spotlight a ship** setting now adds a shared rotating subject, validated AIS facts, optional CC0 Wikidata reference facts and relevant Finnish Portnet previous-port records. All four layouts prioritize the featured marker and name. Field freshness and selection history persist independently. [Implementation and limits](ship-spotlight.md). A dedicated illustrated profile and additional free regional port-call adapters remain future work; complete worldwide origin history is not promised.

## Scaling

Cache JSON at a CDN before adding services. Keep one ingestion leader per provider and durable storage; do not autoscale the AISStream collector per HTTP replica. Evaluate a shared external store or explicit collector/API split only if traffic warrants it. Cloudflare Worker requests/cron are not assumed to be continuous AIS receivers. Durable Objects would require an outbound-WebSocket lifecycle/cost spike before migration.
