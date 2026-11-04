# Genuine AISStream coverage check

[GitHub Actions run 41894534520](https://github.com/nikokoren/port_of_call/actions/runs/41894534520) · 4 November 2026, **20:11:43–20:26:43 Europe/Berlin** (19:11:43–19:26:43 UTC).

One compressed, confirmed connection collected for 900 seconds. **12,380 messages; 4 validation rejects; 2,833 distinct per-area vessel observations in 13 of 15 areas.** No API key, vessel identifiers, ship names or vessel coordinates are retained in this report.

| Area | Distinct observed | Fresh <30m | Named | True heading | Usable orientation |
|---|---:|---:|---:|---:|---:|
| Rotterdam | 865 | 865 | 845 | 318 | 376 |
| Antwerp | 485 | 485 | 466 | 216 | 258 |
| Hamburg | 282 | 282 | 279 | 128 | 129 |
| Bremerhaven | 73 | 73 | 73 | 56 | 56 |
| Felixstowe / Harwich | 22 | 22 | 19 | 16 | 16 |
| Southampton | 105 | 105 | 80 | 36 | 39 |
| Los Angeles / Long Beach | 169 | 169 | 137 | 75 | 86 |
| New York / New Jersey | 183 | 183 | 179 | 127 | 150 |
| Savannah | 30 | 30 | 26 | 17 | 21 |
| Houston — Ship Channel | 96 | 96 | 94 | 79 | 84 |
| Seattle — Elliott Bay | 366 | 366 | 313 | 144 | 151 |
| Charleston | 94 | 94 | 69 | 21 | 33 |
| Singapore | 63 | 63 | 62 | 54 | 57 |
| Shanghai — Yangshan | 0 | 0 | 0 | 0 | 0 |
| Busan — New Port | 0 | 0 | 0 | 0 | 0 |

The first AISStream profile includes the six European areas, six US areas and Singapore. **Shanghai/Yangshan and Busan New Port had no reports during this window and remain unverified/excluded.** A zero sample is not a harbor census or proof of permanent lack of coverage.

Names and headings are AIS self-reports and can be missing. Orientation prefers a valid true heading, then course only when moving at least 0.5 knots. Unknown orientation remains unknown; no category or voyage is inferred.

This single window proves observed account coverage, not an SLA or uninterrupted future delivery. All retained positions were sufficiently recent at capture; the evidence is historical and must not be displayed as current traffic. Public-display/cache/redistribution rights are **not confirmed** by this test or the supplied service-limit table. No public backend was deployed and no community recipe was published.

[Machine-readable aggregate evidence](aisstream-2026-11-04.json) · [Activation steps](../major-ports.md).
