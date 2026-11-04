# Ship Spotlight — feature proposal

Status: researched proposal, not an enabled plugin setting or implemented selection algorithm. Requested 4 November 2026. The existing Harbor Map remains the current display.

## Name and setting

Recommended feature name: **Ship Spotlight**. Recommended boolean setting: **Spotlight a ship**, off by default. This modifies the Harbor Map: one ship receives the strongest marker, its own name/leader label and an information card. Other ships can remain as quiet context. Alternatives: **In Focus** (quieter but less explicit) and **Featured Ship** (clear but less distinctive).

This is a focus option within `display_mode: map`, conceptually `focus_mode: harbor | ship`. A later dedicated vessel illustration/profile layout could still be a separate `spotlight` display mode. Do not expose the switch until the data and layout work end to end.

## What the current source can provide

Checked against AISStream's official `ais-message-models/type-definition.yaml`, 4 November 2026:
https://github.com/aisstream/ais-message-models/blob/291c17682a1108f722c130402089678156613320/type-definition.yaml

The referenced schema file last changed on 3 June 2023; its current contents were retrieved on 4 November 2026. The standard field definitions establish feasibility, not measured current field completeness.

| Fact | Source | Conditions and honest wording |
|---|---|---|
| Current position, speed, course, heading | PositionReport and class-B position reports | Current parser retains these; heading/course may be unavailable. Keep observation time visible. |
| Name and vessel category | Metadata, ShipStaticData, StaticDataReport, ExtendedClassBPositionReport | Current parser retains name and coarse category. The fuller reported type code would support better variety. |
| Reported destination | ShipStaticData.Destination | Crew-entered text; can be stale, abbreviated, non-port text or blank. Label **Reported destination**. Resolve only with a reviewed port/alias catalog; keep ambiguous text unresolved. |
| Reported ETA | ShipStaticData.Eta (Month, Day, Hour, Minute) | No year. Validate unavailable values, dates and UTC/year rollover before display. Label **Reported ETA**; never infer delays or an authoritative schedule. |
| Length and beam | Dimension.A/B/C/D in static and extended class-B messages | Derived from reported distances to the antenna reference point: A+B and C+D. Validate units, unknowns and plausible values before shipping. |
| Draught | ShipStaticData.MaximumStaticDraught | Reported value, not a verified live measurement; verify decoder units/sentinels first. |
| IMO, MMSI, call sign | Static data/envelope | Show only valid identifiers; use IMO/MMSI for enrichment joins, never ship name alone. |
| Reported navigation status | PositionReport.NavigationalStatus | Not in every message class. Reported status is distinct from inferred speed/motion and is not a port call. |
| Previous port / departure port | Not a standard field in these AIS messages | Requires reliable port-call/history data. Do not substitute flag, course, old destination text or proximity to a harbor. |
| Verified flag, age, owner, photographs | Separate registry/licensed reference source | Do not present an MMSI allocation country as independently verified current flag, or a type silhouette as an exact depiction. |

The schema establishes possible fields, not their completeness in our harbor feeds. The previous live probe measured names, type and orientation, not destination/ETA/dimension coverage. Measure those fields in a follow-up counts-only probe before choosing the final card content.

The current implementation intentionally discards destination, ETA, dimensions, draught, IMO/call sign and navigation status. Supporting the focus card requires retaining and validating them, not simply changing the template.

Voyage fields need **their own report timestamps**. The current metadata table merges names/type and receives name context alongside fresh position messages. Adding destination/ETA to that same single-timestamp record would risk making an old destination look freshly reported. Split voyage data or track timestamps per field. Identity can have a longer lifetime than voyage details.

## Where it came from and where it is going

A useful first version can highlight the current ship and show its reported destination plus four to six available facts. Origin remains **unknown** or is omitted unless a source genuinely supplies it. If origin is mandatory for every featured ship, AISStream alone is insufficient.

A lower-cost observational alternative is **Previously seen near [harbor]**, but only when our collector actually observed that vessel there. It must retain its observation date and must never be labeled a confirmed departure/previous port. This would require an explicit bounded history extension; the current latest-position store does not retain it.

A trustworthy **From → To** story needs a licensed port-call/history source plus destination resolution. Enrich only a small set of featured vessels, cache by IMO/MMSI and share results across all installations. This limits request volume; provider pricing and redistribution rights still need evaluation. Do not assume global origin history is free.

For the map, keep the current position geographically exact. A resolved destination can support an overview/inset later. A line connecting ports would be an indicative connection, not an observed voyage track; do not draw a guessed sailing route or infer arrival/departure from an observation rectangle.

## Proposed selection algorithm

Selection runs on the backend over **all eligible observations in the chosen harbor**, before the 40-vessel response cap and pixel decluttering. Rotterdam's measured sample had 865 distinct observations: choosing only among its 40 exported map markers would exclude many possible subjects.

1. **Eligibility first.** Require a valid, recent position (initial focus target: within 15 minutes), a usable name and enough real facts for a card. Exclude expired/invalid records. Unknown categories get no rarity bonus. No suitable candidate means the ordinary harbor overview.
2. **Score useful stories, not just size.** An initial 100-point heuristic could allocate 30 points to usable voyage context, 25 to distinctive size, 20 to activity/new observations, 15 to type variety and 10 to not being featured recently. These are proposal weights to calibrate against real snapshots, not a trained or validated ranking. Use only trusted available inputs. Size should be capped/percentile-based within the harbor, so the biggest permanently moored ship does not always win. "Newly observed" means new to our observation window, not an arrival.
3. **Rotate a strong shortlist.** Select from the best few candidates with a stable, score-weighted choice. A deterministic hash of harbor ID and a time bucket makes the choice reproducible and shared across users. Type penalties/rotation should prevent an endless sequence of cargo ships while preserving data quality.
4. **Hold the subject.** Initial target: retain it for about three hours (roughly 12 standard refreshes). Update its real position/details during that time. Replace it early if it leaves the area or its position becomes too old; never freeze an expired ship merely to fill the slot.
5. **Avoid repeats.** Start with a 24-hour per-harbor cooldown for featured MMSIs. In a small pool, shorten the cooldown or choose the least recently shown suitable vessel. This needs bounded operational selection state, not per-user tracking or a long location history.

Changing label visibility should not change the chosen vessel. Map scale can change the amount of context around the featured position, within the known harbor area. Cache the shared subject by harbor and selection period.

Reserve the featured vessel before response-size truncation and marker/label decluttering. Its real position must remain in the response and visible. Prioritize its name in the existing Hotspots-derived label planner. Use a clear fill/outline/size distinction that works at 1 bit; do not rely on color or animation.

Explain the selection with a short deterministic reason grounded in the data, such as unusual vessel category, substantial reported dimensions, useful voyage details or first feature in this rotation. Do not generate unsupported vessel biographies, destinations or port-call claims.

## Enrichment source research

See [Sources for enriching Port of Call](enrichment-sources.md) for the verified VesselFinder Voyage/Master contract, MarineTraffic/Kpler alternative, free Digitraffic Portnet fields, CC0 Wikidata options, image licenses and port-directory caveats. Public-display rights need to be part of a paid-provider agreement; they are not established merely by buying API credits.

## Delivery order

1. Enrich normalization and field-level freshness; measure actual metadata availability across the 13 covered areas.
2. Implement/test selection, shortlist diversity, cooldown and early replacement on captured real observations.
3. Add the full-screen map/card and compact adaptations using Downstream's native inset design. Compact views show fewer facts, without tiny text.
4. Expose **Spotlight a ship** only when turning it on reliably produces that experience.
5. Add independently sourced previous-port history/registry facts when coverage, cost and rights are verified.

The useful map-and-facts experience is feasible with the current shared stream. Universally reliable origin/destination history is a separate data dependency.
