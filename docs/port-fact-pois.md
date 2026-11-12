# Port facts and map POIs

All **169 port facts** were reviewed on 12 November 2026. The catalog grows from **30 to 97** sourced reference places: **67 additions** across the sixteen harbors. **89 facts** now have at least one associated POI. The complete [fact-by-fact review](port-fact-poi-review.json) retains the original fact, source, accepted places and reasons for exclusions. Coordinates come from verified Wikidata entities under CC0; no per-installation lookup or paid service is added.

## Show the place mentioned in the fact

The backend orders the current fact's associated POIs first and marks them `fact_related`. When **Show port facts?** is enabled and the fact is actually visible in the layout, the client gives its POI first chance at label space before ordinary ship-name labels. The same association rotates with the fact, including multi-harbor rotations and Finnish snapshots forwarded through the world backend. Multiple facts can reference the same place: both Ballard Locks blurbs select Ballard Locks.

Vessel hulls, Spotlight, the port card and credits remain protected. The map keeps its fixed camera. A related POI can still be omitted if its coordinate is outside the screen, its pin overlaps a hull, or no clear label fits. Other POIs fill available space after ship labels. If facts are disabled or hidden by a small layout, no special label space is reserved. Harbor POIs remain built in, with no additional setting. The existing limit of **one or two visible POIs** remains; up to eight source candidates are supplied, not 97 labels on a screen.

## Additions by harbor

| Harbor | Added | Places |
|---|---:|---|
| Helsinki | 5 | Katajanokka, Vuosaari Harbour, Old Market Hall, Olympia Terminal, Market Square |
| Turku | 5 | Meyer Turku shipyard, Suomen Joutsen museum, Föri ferry crossing, Sigyn museum, Forum Marinum |
| Rauma | 5 | Old Rauma, Rauma shipyard, Maritime Museum, Kylmäpihlaja lighthouse, Marela museum |
| Rotterdam | 5 | Maasvlakte 2, Erasmus Bridge, SS Rotterdam hotel, Maasvlakte, Maritime Museum |
| Antwerp | 5 | Port House, Het Steen, Kieldrecht Lock, Sint-Anna tunnel, Bonapartedok |
| Hamburg | 7 | Speicherstadt, Elbphilharmonie, Old Elbe Tunnel, Willkomm-Höft, Rickmer Rickmers museum, Fish Market, Maritime Museum |
| Bremerhaven | 6 | Emigration Center, Maritime Museum, Wilhelm Bauer museum, Bremerhaven lighthouse, Fischereihafen, Container Terminal |
| Felixstowe / Harwich | 2 | Harwich Redoubt, Harwich ferry terminal |
| Southampton | 1 | Town walls |
| Los Angeles / Long Beach | 6 | Queen Mary museum, Angels Gate Lighthouse, USS Iowa museum, Point Fermin Lighthouse, Lane Victory museum, Terminal Island |
| New York / New Jersey | 6 | Port Newark, Ellis Island, Bayonne Bridge, Intrepid Museum, South Street Seaport, Brooklyn Navy Yard |
| Savannah | 2 | River Street, Tybee Lighthouse |
| Houston | 2 | Lynchburg ferry crossing, Barbours Cut |
| Seattle | 3 | Ballard Locks, Space Needle, Fishermen’s Terminal |
| Charleston | 4 | Patriots Point / Yorktown, Rainbow Row, Morris Island Lighthouse, Charleston Navy Yard |
| Singapore | 3 | Raffles Lighthouse, Marina Barrage, Jurong Island |

Museum names describe fixed display sites, never a real-time AIS fix. Ferry crossings name the fixed crossing, not the ferry's changing position. Neighborhoods and islands use a geographic representative point. All POIs use the existing pin icon and native small-label typography.

## What was left out

- Harwich's Treadwheel Crane and Ha’penny Pier, Savannah's Garden City Terminal, and Charleston's Wando Welch Terminal need a suitable verified site coordinate. They are recorded as candidates, with no invented point.
- The English Tuas Port title resolved to the entire Port of Singapore, not the actual Tuas site. That coordinate was rejected. The similarly ambiguous Port House and Marela searches were corrected to the Antwerp and Rauma entities before inclusion.
- Operating ships such as Polarstern and Shieldhall do not become fixed map points. Historical voyages, people, operators, broad river routes and distant destinations are not pinned as local sites. Horsburgh Lighthouse is too far east for the curated Singapore view. Full per-fact reasons are retained in the review.

The [source catalog](landmark-sources.json) retains coordinates, entity URLs and fact associations. [The refresh script](../scripts/build_landmarks.py) uses explicitly reviewed entity IDs, preferred Earth-coordinate claims and a harbor-vicinity check; it rejects ambiguity and only stages a review file. It does not silently overwrite the production catalog. [Its input](../scripts/landmark_catalog.json) includes the five withheld candidates.

## Verification and preview provenance

Python checks cover every fact's review, every association, source parity, harbor vicinity, bounded candidate counts, current-fact priority, rotation periods and ambiguous coordinate rejection. Browser reference scenarios check the actual label order, geographic pin anchors, clearance, counts, dark mode, Spotlight and small layouts, including facts switched off. No AIS positions or timestamps are fabricated or modified.

The screenshots select a **reviewed static fact** alongside genuine **archived** observations. They illustrate fact/POI combinations, rather than claiming that the fact was selected at the capture's historical hour. Preview pages explicitly say POI REFERENCE TEST. The source captures are:

- [seattle-candidates](../fixtures/seattle-candidates.json): 12 November 2026, 09:19:04 CET.
- [seattle-candidates-spotlight](../fixtures/seattle-candidates-spotlight.json): 12 November 2026, 09:19:41 CET.
- [hamburg-pois](../fixtures/hamburg-pois.json): 12 November 2026, 10:04:01 CET.
- [helsinki-pois](../fixtures/helsinki-pois.json): 12 November 2026, 10:05:06 CET.
- [turku-pois](../fixtures/turku-pois.json): 12 November 2026, 10:05:06 CET.
- [rauma-pois](../fixtures/rauma-pois.json): 12 November 2026, 10:05:06 CET.

[Ballard Locks](screenshots/poi-seattle-locks.png) · [Space Needle](screenshots/poi-seattle-needle.png) · [Elbphilharmonie](screenshots/poi-hamburg-hall.png) · [Reference results](screenshots/results-poi-facts.json).

Reproduce with the preview and asset-relay servers running:

```sh
PLAYWRIGHT_EXECUTABLE_PATH=/usr/bin/chromium MAP_RELAY=true node scripts/check-poi-facts.mjs
```

Update **Shared and all four layouts** using the [copy/paste guide](copy-paste.md) for the stronger fact-related label priority. The expanded catalog and fact associations are served automatically by the backend. Settings and polling URLs stay the same.
