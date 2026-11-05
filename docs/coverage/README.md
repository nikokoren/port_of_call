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

## Spotlight field follow-up · 5 November 2026

[GitHub Actions run 41997213848](https://github.com/nikokoren/port_of_call/actions/runs/41997213848), **09:47:52–09:49:52 Europe/Berlin** (08:47:52–08:49:52 UTC). One compressed, confirmed connection; **120 seconds, 1,614 messages, one validation reject**. The repository secret stayed on the runner. This follow-up retains only aggregate counts, not vessel records.

The cold-start sample observed **833 distinct current per-area observations** across the same 13 positive areas and **93 suitable Spotlight candidates in 10 areas**. Counts reflect validated values joined to actual current positions. A short two-minute sample does not collect every ship's less-frequent static report. New York, Singapore and Felixstowe had positions but no qualifying Spotlight subject during this window: the feature correctly falls back to the ordinary map. Continuous collection builds the metadata cache; no area is added or removed automatically.

| Area | Current positions | Spotlight eligible | Valid IMO | Reported destination | ETA | Length | Draught |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rotterdam | 265 | 35 | 18 | 30 | 27 | 34 | 27 |
| Antwerp | 125 | 8 | 1 | 4 | 8 | 6 | 7 |
| Hamburg | 124 | 28 | 4 | 20 | 11 | 26 | 21 |
| Bremerhaven | 26 | 2 | 1 | 2 | 2 | 2 | 2 |
| Felixstowe / Harwich | 6 | 0 | 0 | 0 | 0 | 1 | 0 |
| Southampton | 28 | 1 | 1 | 1 | 1 | 2 | 1 |
| Los Angeles / Long Beach | 34 | 5 | 2 | 5 | 4 | 5 | 4 |
| New York / New Jersey | 44 | 0 | 0 | 0 | 0 | 0 | 0 |
| Savannah | 8 | 1 | 1 | 1 | 1 | 1 | 1 |
| Houston — Ship Channel | 47 | 2 | 0 | 2 | 2 | 2 | 2 |
| Seattle — Elliott Bay | 102 | 10 | 4 | 5 | 2 | 13 | 4 |
| Charleston | 14 | 1 | 0 | 0 | 0 | 2 | 1 |
| Singapore | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| Shanghai — Yangshan | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Busan — New Port | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

These are availability counts, not validation of crew-entered voyage claims, a complete port census or an uptime guarantee. Unknown identifiers, sentinel dimensions/draught and malformed ETAs are excluded. No port-call event is inferred. Public-display/cache rights remain unconfirmed. [Machine-readable follow-up](aisstream-spotlight-2026-11-05.json).
