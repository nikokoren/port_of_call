# Bundled destination names

The backend contains **40,926 unambiguous coded-location names** and **247 country labels**, retrieved on **11 November 2026** from Wikidata structured data (CC0). Exact matches are available immediately without a request per ship or per installation. This is a location-name reference, not an authoritative port-call feed or an expansion of the sixteen live harbor areas.

The data is in [`_locode_data.py`](../port_of_call/_locode_data.py), with entity IDs retained per record. It is one sorted string, searched by [`port_reference.py`](../port_of_call/port_reference.py), rather than a large Python dictionary in each collector. The string occupies about 2 MB in CPython, with a bounded 256-row lookup cache. No coordinates are bundled or applied to vessel markers. Native Cloudflare checks cover the production build.

## Sources and reuse

- [Wikidata licensing: CC0 structured data](https://www.wikidata.org/wiki/Wikidata:Licensing).
- Coded locations: public [QLever Wikidata mirror](https://qlever.dev/wikidata), export endpoint `https://qlever.dev/api/wikidata` with `action=tsv_export`.
- Country labels: official [Wikidata query service](https://query.wikidata.org/), TSV export.
- [Snapshot manifest](port-reference-snapshot.json): exact queries, retrieval date, input/output hashes, counts and ambiguity exclusions. A mirror snapshot can lag the live graph; retrieval date does not assert all entries were updated on that date.

The original UNECE/UNLOCODE directory was considered but not bundled: its generic site terms and the standards footer give conflicting reuse signals, and the DataHub mirror explicitly says its PDDL notice does not cover the underlying list. The reference here uses CC0 Wikidata claims instead.

## Admission and lookup rules

Each accepted code has one exact Wikidata entity with an English label, a valid current ISO country prefix and a valid three-character location code. Conflicting entity matches are excluded. Airport/aerodrome entities are excluded by class hierarchy, with an additional name check; they must not become purported shipping destinations. This still includes cities and other transport locations, so a crew-entered code is not independent proof of its intended voyage.

Reviewed local aliases take precedence, followed by valid cached exact live matches, then the bundled reference. For example `USORF` resolves to Norfolk, `DEBRB` to Brunsbüttel and `JPKRE` to Kure. The reviewed `GBIMM` alias resolves Immingham: both its town and port have the code, and the port entity explicitly verifies it. Some codes remain unresolved: `CNSHA` has an airport-only match in this snapshot, so the app does not label a ship as heading for that airport.

Displayed unresolved codes still enter the primary background lookup queue. Live Wikidata lookups accept a unique exact code and usable English name without requiring coordinates. Invalid, absent or conflicting coordinates are omitted. Old negative results from the coordinate-required resolver are reconsidered without discarding positive ship caches. New absent/ambiguous matches remain cached for seven days and transient failures for one hour; unknown free text is never guessed into a port.

## Rebuild

Export the two queries in the manifest as complete TSV files with columns `?item`, `?code`, `?name`. The location query excludes items whose instance/subclass hierarchy reaches aerodrome `Q62447`. The builder applies additional validation and excludes conflicting code mappings.

```sh
python scripts/build_port_reference.py \
  --locations /path/to/locations.tsv \
  --countries /path/to/countries.tsv \
  --date YYYY-MM-DD
```

Review the manifest/count changes, run tests, and stage the reference with `python scripts/prepare_cloudflare.py`. The updater is a maintenance command, not a runtime fetch or automatic unreviewed data update.
