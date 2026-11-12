# Copy the recipe into TRMNL

The files on GitHub are ready to paste into your private plugin. Open a file, then use GitHub’s **Copy raw file** button. The checked-in settings use the live world backend, including the three Finnish ports.

| TRMNL editor | GitHub source |
|---|---|
| Custom Fields | [custom_fields.yml](../custom_fields.yml) — paste the entire file |
| Shared | [shared.liquid](../shared.liquid) |
| Full | [full.liquid](../full.liquid) |
| Half Horizontal | [half_horizontal.liquid](../half_horizontal.liquid) |
| Half Vertical | [half_vertical.liquid](../half_vertical.liquid) |
| Quadrant | [quadrant.liquid](../quadrant.liquid) |

Use [settings.yml](../settings.yml) for the other plugin settings: polling strategy, GET, 15-minute refresh, framework 3.4.4, and no screen padding. Copy the `polling_url` value into TRMNL’s URL field, without the YAML key or surrounding quotes:

```liquid
https://port-of-call-world.5g5wqr7kzx-466.workers.dev/api/v1/vessels?harbors={{ harbor | join: ',' }}&spotlight={{ ship_spotlight }}&format=map
```

Save the fields and templates, then choose your harbors and refresh. Leaving the harbor selection empty cycles through all sixteen; selecting one keeps that port. Ship labels, Spotlight, port facts and the vessel legend are optional settings. Harbor landmarks are built into the map and add up to two sourced features when space permits. Spotlight adds a short trail once enough genuine position history is available. **Show map legend** adds a compact icon-and-text key at the bottom beside the port card, above the map credits, on full-screen maps only. The map stays on the curated harbor view when Spotlight is enabled.

For future recipe updates, copy the changed files into the same editor tabs. When maintaining the field definitions in this repository, edit `settings.yml` and run `python scripts/sync_custom_fields.py` to refresh the standalone field array. The tests check that both definitions agree.

The vessel count now distinguishes the observation area from the actual drawn ships, for example **322 vessels in area · 19 on map**. Update all four layout tabs and Shared for this count, trails and landmarks. Harbor rotation and richer free reference facts are supplied by the backend.

The map format supplies up to **80 candidate vessels** using compact records, within the same 15 KB response budget. The screen draws those that fit without crowding; label limits remain unchanged. To upgrade an existing plugin safely, paste **Shared and all four layouts first**, then append `&format=map` to its polling URL. The updated templates accept both formats. The old URL continues to serve the original 40-candidate format. No custom-field or credential changes are needed.
