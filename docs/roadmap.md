# Roadmap

V1 ships a map of recently reported positions. First stabilize Finnish operation with private TRMNL tests and multi-day monitoring. Extend the harbor registry only with provider coverage and license evidence; subscription quotas are an operator concern, never a setting for recipe users.

## V2 · Arrivals & Departures

Add a licensed official port-call/schedule provider through a separate adapter and versioned `/api/v1/harbors/{id}/port-calls` contract. Explore Digitraffic Portnet/NEMO for Finland and separately evaluate API.SH, Searoutes, VesselFinder or official port APIs for other countries. Verify price, ship-name completeness, API rate limits, timestamp semantics and public redistribution before selection. No API.SH approximate positions should drive map markers.

Keep expected/actual time, timezone, event type and source status separate. Mark unknown explicitly. A position inside a rectangle cannot establish a berth, authoritative arrival, departure, delay or ETA. Do not turn AIS destination text into a schedule. Add the `board` display setting only when a genuine schedule layout and its tests work in all sizes.

## V3 · Vessel Spotlight

Reuse MMSI-keyed static metadata but add reliable flag/dimensions/voyage adapters and field provenance. A type silhouette must be labeled as such; exact vessel depictions/photos need separate rights. Unavailable metadata is omitted. No generated educational facts or unsupported voyage claims. Add a dedicated `spotlight` payload and layout after its source is verified.

## Scaling

Cache JSON at a CDN before adding services. Keep one ingestion leader per provider and durable storage; do not autoscale the AISStream collector per HTTP replica. Evaluate a shared external store or explicit collector/API split only if traffic warrants it. Cloudflare Worker requests/cron are not assumed to be continuous AIS receivers. Durable Objects would require an outbound-WebSocket lifecycle/cost spike before migration.
