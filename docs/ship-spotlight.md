# Ship Spotlight

Implemented 5 November 2026. **Free data sources only**: existing AIS, CC0 Wikidata and CC BY 4.0 Digitraffic Portnet. No paid subscription, credits, trial or per-installation data key.

## Use it

Turn on **Spotlight a ship** in the Harbor Map settings. The same harbor shares one subject across installations and framing choices. Labels can remain off: the featured name is always prioritized. Turn the switch off for the ordinary harbor overview. No suitable fresh candidate means an explicit overview fallback, never a frozen or invented ship.

The full native map card shows reported destination, reported previous port where available, reported ETA, up to six AIS facts and two optional reference facts. Half layouts reduce the facts; the quadrant keeps identity, destination and two short facts beside the map. The stronger hull and inverted name label work at one bit. Marker positions are never displaced to make room for text.

## What the facts mean

- Positions, speed, heading/course and navigation status retain the dynamic report time. Focus requires a position younger than 15 minutes and a feed younger than the configured freshness threshold.
- IMO numbers require the seven-digit checksum. Unknown/saturated dimensions and draught, malformed ETAs and unavailable text are omitted. Length/beam derive from antenna distances. Digitraffic draught is decimetres converted to metres; AISStream's decoded floating-point draught is metres, not divided again. AIS ETA has no year; the card says so and never infers a schedule or delay.
- Destination, ETA and draught expire independently after six hours. Identity/dimensions expire after seven days. Each field retains its source and report timestamp. A new position/name cannot refresh a destination; out-of-order static messages cannot overwrite newer facts. An explicit unknown clears a previous value. A crew can keep broadcasting an obsolete destination or ETA: even a recent report is not independent voyage confirmation.
- Previous port is absent from standard AIS. The optional Finnish Portnet join requires an exact IMO or MMSI, the selected Finnish port, a recent record with an actual arrival before the observation, and no actual departure before it. An IMO mismatch rejects the record even if MMSI matches. Planned calls and old calls elsewhere do not supply origin. This is a **reported previous port**, not a reconstructed voyage. Otherwise the full card says unknown.
- Wikidata ship lookup requires a unique exact IMO statement. It can add class, builder, operator and service-entry year. Deprecated and ended-role statements are excluded; reference information is not a verified current commercial registry. It does not provide a verified flag or build year. Port lookup requires a unique exact UN/LOCODE, an English label and Earth coordinates. Ambiguous destinations remain raw reported text. A small reviewed exact alias catalog avoids unnecessary lookups. There are no fuzzy ship-name joins, guessed tracks, inferred origins or photo-license assumptions.

The JSON card retains identifiers, sources and timestamps even when the compact display omits some facts. Destination coordinates are optional reference metadata; no straight line is presented as a sailing route. No personal/agent/customs fields from Portnet are retained.

## Selection

`port_of_call/spotlight.py` evaluates every eligible observation within the reviewed harbor box **before** the 40-marker cap. Eligibility requires a fresh position, a name and at least two available facts (including the reported category). Previous port and Wikidata are not prerequisites.

A transparent heuristic scores metadata quality (up to 30), capped local length percentile (25), time since last feature (20), category variety (15) and reported motion (10). Unknown categories receive no variety bonus. The best five form a score-weighted deterministic choice seeded by harbor and three-hour UTC bucket. This is a heuristic, not a learned or validated measure of human interest.

SQLite holds the subject for up to three hours, survives restart and replaces it early if it leaves the area or becomes stale/ineligible. The 24-hour MMSI cooldown relaxes only when all suitable candidates have already featured. At most 64 per-harbor history entries retain MMSI, category and selection time; no visitor data or position history. A short data-grounded reason explains selection.

The chosen ship is first in the snapshot and protected from count/byte truncation. The map camera reserves space beside/above the card, then centers the subject in that free space; its marker remains at the exact projected coordinate. Other ships yield during decluttering. The Hotspots-derived label planner prioritizes the featured name even when ordinary labels are off.

## Free enrichment operations

One asynchronous worker shares the ingestion process and SQLite database. HTTP snapshot generation uses cached data only. Queue capacity is 128 unique pending keys. Wikidata requests are spaced by at least one second, with a persisted hard cap of 500 requests/day across the service, independent of installations. Positive results cache 30 days, absent/ambiguous matches seven days and transient failures one hour. There is no account or charge fallback. All structured facts link to their entity and CC0; a cached hit preserves its original fetch date.

Portnet is polled at most once/hour only for the Finnish provider, with failure backoff. Only the relevant Finnish calls' identifiers, port codes and actual event times are stored, for at most seven days. Source credit and CC BY 4.0 remain visible. Optional-source failures cannot stop AIS collection or block a map response. Run one ingestion/enrichment leader as documented; multiple independent replicas are not the supported deployment.

## Evidence and limits

`fixtures/*-spotlight.json` are genuine historical free-source captures from **5 November 2026, 08:28 UTC**, visibly labeled Archive in previews, never served by the public backend. The capture found 54/54 suitable Helsinki observations, 24/25 Turku and 17/18 Rauma. Those denominators are time-limited observations, not port traffic totals. `fixtures/spotlight-metrics.json` records richer field availability. PLYCA's current Rauma Portnet record supplied reported previous port Hanko; its reported destination code resolved to Tilbury through Wikidata. Other subjects correctly retain unknown origin. The collector also found exact IMO reference matches for the selected vessels.

The 13-area AISStream profile uses the same normalization and selector, with offline decoder/selection tests. The earlier live coverage probe measured basic metadata, not these richer fields; worldwide field completeness and long-term reliability remain unmeasured. AISStream public display/cache rights and a public always-on host remain separate deployment requirements. No public TRMNL import/device test is claimed.

Refresh these archive examples explicitly with `.venv/bin/python scripts/capture_spotlight.py`. This overwrites only the Spotlight fixtures/metrics, not the original overview captures. Run the Python and Node suites and browser screenshots as described in the repository README.
