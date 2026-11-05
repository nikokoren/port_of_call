# Ship Spotlight: proposed content ranking

Review order updated 5 November 2026 after the requested extended-label design. This is a recommendation, not a requirement to display every field. The ship's **name is always the headline**; observation time remains in the harbor key/API and is omitted from the ship overlay. Sources must remain free.

| Rank | Fact | Why it earns space | Availability / honest wording |
|---|---|---|---|
| 1 | Reported previous port → destination | The clearest human story: where this ship has come from and where it says it is going. | Destination is reported AIS text. Previous port requires a relevant actual Finnish Portnet call; otherwise show the reported destination alone. No inferred origin or sailing track. |
| 2 | Length × beam | An immediate, impressive sense of scale; the most useful numerical fact. | Derived from valid reported antenna distances. If only length is available, show length. Local comparisons could refer only to ships we actually observed with known dimensions. |
| 3 | Specific vessel type / class | Explains what makes the vessel distinctive: tug, dredger, rescue vessel, ferry or a known class. | AIS type codes, with optional exact-IMO Wikidata class facts. Generic cargo/tanker is less distinctive; do not invent a subtype. |
| 4 | Speed | A recent, changing fact that tells the viewer whether this ship is moving. | Timestamped AIS speed over ground in knots. Zero remains zero; speed alone does not establish an arrival, departure or anchorage. |
| 5 | Service-entry year / years in service | Provides a story for older ships and recognizable ferries. | Optional exact-IMO Wikidata reference fact. The current cache retains service-entry year; it is not a verified build year, and a year-only date cannot give an exact anniversary age. |
| 6 | Operator | A recognizable company can make an otherwise unfamiliar ship interesting. | Optional Wikidata fact, excluding deprecated and ended-role statements. Treat it as a reference listing rather than a verified current commercial registry. |
| 7 | Reported ETA | Adds a sense of the ship's plans. | Crew-entered AIS month/day/time, without a year. It may be obsolete even when recently rebroadcast. Never turn it into a confirmed schedule or delay. |
| 8 | Reported navigation status | Distinguishes moored, anchored, under way and other reported states. | Available in some position messages; explicit unknowns are omitted. Status is not independent confirmation of a port event. |
| 9 | Reported draught | Interesting technical detail about the vessel's reported immersion. | Validated static AIS metres; can be stale and is not a verified live measurement. No clearance calculations. |
| 10 | Builder | An occasional historical hook for a notable ship. | Optional exact-IMO Wikidata reference fact; lower priority in a small overlay. |

The first compact version uses **name + type, reported ports, length/beam and speed**, with explicit category labels and port countries. It shows only available values. The bottom-left Port of Call harbor card remains separate. Ranks 5–10 remain available in the backend or research model, rather than all being squeezed into the annotation. Field choices can change after user review without changing the vessel-selection algorithm.

IMO, MMSI and call sign remain available in the API for identification but have little everyday display value. Cargo capacity, passenger capacity, tonnage and independently verified build dates are promising future candidates; they are not currently collected or promised by this implementation. No paid source is a fallback.

## Accepted presentation update

The overlay now uses white text on black, separate Reported from / Reported to lines with country names, explicit Type and Length/width captions, and Speed expressed in knots. There is no position-time footer. Larger layouts additionally show available Flag (AIS) / Reported flag / Registry (Wikidata), Built in / Shipyard country, and a plausible Reported ETA. Country information takes priority over a builder company name; compact layouts omit optional extras to retain readable type and voyage information. ETA year inference and country-source distinctions are documented in [Ship Spotlight](ship-spotlight.md#country-labels-and-eta-inference--5-november-follow-up).
