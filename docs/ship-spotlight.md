# Ship Spotlight

Implemented 5 November 2026. **Free data sources only**: existing AIS, CC0 Wikidata and CC BY 4.0 Digitraffic Portnet. No paid subscription, credits, trial or per-installation data key.

## Use it

Turn on **Spotlight a ship** in the Harbor Map settings. The same harbor shares one subject across installations and framing choices. Labels can remain off: the featured name is always prioritized. Turn the switch off for the ordinary harbor overview. No suitable fresh candidate means an explicit overview fallback, never a frozen or invented ship.

The **Port of Call harbor card stays at bottom left**. Spotlight is a separate floating annotation: a larger ship-name label, reported type, reported ports where known, length/beam, speed and a position-time footer. A mandatory connector links it to the solid black featured vessel. It finds room on the map without covering that ship, the harbor card or map credit. Other ships remain visible in lighter grey and can be covered by the annotation when necessary; one-bit views use hollow context hulls. Marker positions are never displaced to make room for text. Compact harbor cards preserve the harbor name, report count, update time and source credit.

The [ranked fact proposal](ship-spotlight-content.md) explains which facts are most interesting, their free-source limitations and the provisional shortlist for user review. The API still retains the richer facts and reference enrichment; the overlay deliberately shows a small subset.

## What the facts mean

- Positions, speed, heading/course and navigation status retain the dynamic report time. Focus requires a position younger than 15 minutes and a feed younger than the configured freshness threshold.
- IMO numbers require the seven-digit checksum. Unknown/saturated dimensions and draught, malformed ETAs and unavailable text are omitted. Length/beam derive from antenna distances. Digitraffic draught is decimetres converted to metres; AISStream's decoded floating-point draught is metres, not divided again. AIS ETA has no year; the API retains its reported form without inferring a schedule or delay. It is outside the provisional overlay shortlist.
- Destination, ETA and draught expire independently after six hours. Identity/dimensions expire after seven days. Each field retains its source and report timestamp. A new position/name cannot refresh a destination; out-of-order static messages cannot overwrite newer facts. An explicit unknown clears a previous value. A crew can keep broadcasting an obsolete destination or ETA: even a recent report is not independent voyage confirmation.
- Previous port is absent from standard AIS. The optional Finnish Portnet join requires an exact IMO or MMSI, the selected Finnish port, a recent record with an actual arrival before the observation, and no actual departure before it. An IMO mismatch rejects the record even if MMSI matches. Planned calls and old calls elsewhere do not supply origin. This is a **reported previous port**, not a reconstructed voyage. Otherwise origin remains unknown in the API and the overlay shows only the reported destination.
- Wikidata ship lookup requires a unique exact IMO statement. It can add class, builder, operator and service-entry year. Deprecated and ended-role statements are excluded; reference information is not a verified current commercial registry. It does not provide a verified flag or build year. Port lookup requires a unique exact UN/LOCODE, an English label and Earth coordinates. Ambiguous destinations remain raw reported text. A small reviewed exact alias catalog avoids unnecessary lookups. There are no fuzzy ship-name joins, guessed tracks, inferred origins or photo-license assumptions.

The JSON card retains identifiers, sources and timestamps even when the compact display omits some facts. Destination coordinates are optional reference metadata; no straight line is presented as a sailing route. No personal/agent/customs fields from Portnet are retained.

## Selection

`port_of_call/spotlight.py` evaluates every eligible observation within the reviewed harbor box **before** the 40-marker cap. Eligibility requires a fresh position, a name and at least two available facts (including the reported category). Previous port and Wikidata are not prerequisites.

A transparent heuristic scores metadata quality (up to 30), capped local length percentile (25), time since last feature (20), category variety (15) and reported motion (10). Unknown categories receive no variety bonus. The best five form a score-weighted deterministic choice seeded by harbor and three-hour UTC bucket. This is a heuristic, not a learned or validated measure of human interest.

SQLite holds the subject for up to three hours, survives restart and replaces it early if it leaves the area or becomes stale/ineligible. The 24-hour MMSI cooldown relaxes only when all suitable candidates have already featured. At most 64 per-harbor history entries retain MMSI, category and selection time; no visitor data or position history. A short data-grounded reason explains selection.

The chosen ship is first in the snapshot and protected from count/byte truncation. The map camera reserves space beside/above the harbor card; its subject marker remains at the exact projected coordinate. An extension of the Hotspots-derived label planner evaluates open screen positions for the larger annotation, always drawing a connector. Harbor information, map attribution and the featured hull are hard obstacles. Context ships are soft obstacles: covering them has a cost, but is allowed. The planner prefers a nearby empty area and avoids fixed overlays along the connector. The ordinary name-label pass avoids both cards and the featured connector. The selected annotation remains visible even when ordinary names are off.

If a compact frame cannot fit the annotation near the initial anchor, the camera shifts to the nearest tested position that gives both overlays room. Only the camera moves: the hull still uses the real map projection. Background hulls are smaller and grey; fully covered hulls do not contribute to the displayed shown count. Annotation opacity is used while measuring native text, since visibility-hidden ancestors make the native clamp cache empty text. Visual checks require readable overlay text, a visible headline, a connected endpoint and the preserved harbor card, in addition to ordinary projection/collision checks.

## Free enrichment operations

One asynchronous worker shares the ingestion process and SQLite database. HTTP snapshot generation uses cached data only. Queue capacity is 128 unique pending keys. Wikidata requests are spaced by at least one second, with a persisted hard cap of 500 requests/day across the service, independent of installations. Positive results cache 30 days, absent/ambiguous matches seven days and transient failures one hour. There is no account or charge fallback. All structured facts link to their entity and CC0; a cached hit preserves its original fetch date.

Portnet is polled at most once/hour only for the Finnish provider, with failure backoff. Only the relevant Finnish calls' identifiers, port codes and actual event times are stored, for at most seven days. Source credit and CC BY 4.0 remain visible. Optional-source failures cannot stop AIS collection or block a map response. Run one ingestion/enrichment leader as documented; multiple independent replicas are not the supported deployment.

## Evidence and limits

`fixtures/*-spotlight.json` are genuine historical free-source captures from **5 November 2026, 08:28 UTC**, visibly labeled Archive in previews, never served by the public backend. The capture found 54/54 suitable Helsinki observations, 24/25 Turku and 17/18 Rauma. Those denominators are time-limited observations, not port traffic totals. `fixtures/spotlight-metrics.json` records richer field availability. PLYCA's current Rauma Portnet record supplied reported previous port Hanko; its reported destination code resolved to Tilbury through Wikidata. Other subjects correctly retain unknown origin. The collector also found exact IMO reference matches for the selected vessels.

The 13-area AISStream profile uses the same normalization and selector, with offline decoder/selection tests. A subsequent [120-second live follow-up](coverage/README.md#spotlight-field-follow-up--5-november-2026) measured the richer fields: 833 current per-area observations and 93 eligible subjects across ten areas. All 13 covered areas supplied positions, but three lacked enough static facts in this short cold-start window and correctly use overview fallback. This is partial field-availability evidence, not complete coverage or a long-term reliability study. AISStream public display/cache rights and a public always-on host remain separate deployment requirements. No public TRMNL import/device test is claimed.

Refresh these archive examples explicitly with `.venv/bin/python scripts/capture_spotlight.py`. This overwrites only the Spotlight fixtures/metrics, not the original overview captures. Run the Python and Node suites and browser screenshots as described in the repository README.
