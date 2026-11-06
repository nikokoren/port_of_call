# Optional rotating port facts

**Show port facts?** is off by default. When enabled, one short blurb appears below the vessel count. Selection advances on the hour (UTC), shared across installations; a normal device refresh picks up the change. These are static geography/history/port facts, separate from live traffic.

The collection covers every verified Finnish and AISStream harbor: four facts per port, 64 in total, reviewed by the maintainer. Each figure was checked against the linked source; claims the sources did not support were reworded or replaced before review. All are original factual summaries. The [source module](../port_of_call/port_facts.py) retains a reference URL for every text. API `port_fact` contains `id`, `text` and `source_url`; no extra upstream requests are made for rotation. Adding facts means editing that reviewed collection, with its source, rather than accepting unverified generated claims.

All four layouts use native labels and clamping. The smallest OG half-horizontal and quadrant layouts omit the blurb using native responsive visibility; larger X versions have room. The port card remains at the bottom-left. Under the shared 15 KB response budget, optional blurbs are removed before voyage labels or vessel positions.

Examples: [overview](screenshots/facts-full.png), [dark Spotlight](screenshots/facts-full-dark.png), [half vertical](screenshots/facts-half-vertical.png), [X quadrant](screenshots/facts-x-quadrant.png). These are historical 5 November 2026 vessel captures with curated port facts, not current traffic.

## Other destination and provenance copy

`LVMRX` is the exact UN/LOCODE for **Mērsrags, Latvia**, checked against the UNECE code-list CSV mirror (`LV`, `MRX`, Mersrags). The resolver supplies a name/country only; it does not invent a ship position or previous port. Reference: https://service.unece.org/trade/locode/lv.htm and https://github.com/datasets/un-locode/blob/main/data/code-list.csv.

`FAIRWAY WORKS` is a free-text activity in the destination field, meaning work on navigable shipping channels. Only that exact normalized phrase is rendered as **Activity: Fairway works**; it is not resolved as a destination port or made into a route arrow. It does not tell us the ship's precise work assignment. Other unknown free text is preserved without guessing.

The visible flag line omits the `(AIS)` qualifier. The API retains original values, inference method and provenance. Footer credits use native inline `map__attribution` spans; each wrapped text fragment receives the native canvas background, while the containing layout row is transparent.
