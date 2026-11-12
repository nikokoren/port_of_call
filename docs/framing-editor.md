# Harbor framing editor

[Open the editor](https://nikokoren.github.io/port_of_call/framing/) to adjust a draft for all sixteen harbors. Every reviewed POI is available on the map and in the sidebar: 97 places in total. The map uses the pinned native TRMNL 3.4.4 runtime, the actual full-layout markup, port card, font assets and map tiles. This is a **map-only review**, with no vessel data or simulated maritime activity.

1. Select a harbor, **OG** or **X**, and landscape or portrait.
2. Drag to pan. Use the zoom field or + / −. **Fit POIs** fits the selected harbor's places using the native integer-zoom helper.
3. Preview different port facts to see which place is associated and how much space the card occupies. All POIs remain available for framing; the live recipe still draws only one or two where space permits.
4. The dashed outline shows current vessel-data coverage. Moving the view does not expand the AIS subscription or invent positions outside that area.
5. Drafts save in your browser. Use **Copy changes** or **Copy draft link**, then paste the result into the chat to apply the reviewed framing.

OG and X drafts are independent. Orientation changes the preview dimensions while retaining that device's focus and zoom. **Copy framing to X/OG** explicitly copies the current camera to the other profile. **Reset this view** restores only the selected port/device. The editor never writes the production registry, changes backend cameras or deploys edits.

The focus coordinate is the harbor anchor in the clear part of the map, beside or above the port card. It differs from the visible map center when the card occupies space. The editor accounts for that offset when exporting a drag, so loading a draft reproduces its framing. The standard preview uses OG 800×480 at 1-bit, and X 1040×780 logical pixels scaled by the native framework to 1872×1404 at 4-bit; portrait swaps the dimensions. **Fit to window** changes only the editor's display scale.

## Can zoom be fractional?

The native **helpers use whole numbers** in the pinned framework:

- `TRMNLMaps.options({zoom})` uses `Math.round`: 10.5 becomes 11; 11.25 becomes 11.
- `TRMNLMaps.fit()` floors its computed zoom to an integer, then snaps the camera to the pixel grid.
- Native center snapping and the dither world-origin calculation skip fractional zooms.

This is a helper/design constraint, not a MapLibre limitation. Our recipe's fixed-camera branch calls MapLibre `jumpTo()` directly. It can retain **10.5 and 11.25**; both values were verified after `TRMNLMaps.ready()` completed in Chromium. [Pinned options/fit source](https://github.com/usetrmnl/trmnl-framework/blob/1aa4dde1436e1359a011093cb5b586f0fc3c0cca/public/js/3.4.4/plugins.js#L6900) · [Center and dither-origin code](https://github.com/usetrmnl/trmnl-framework/blob/1aa4dde1436e1359a011093cb5b586f0fc3c0cca/public/js/3.4.4/plugins.js#L6352).

Whole-number steps are the default in the editor. **Allow quarter-step zoom** explicitly enables fractional previews, including decimal-comma input such as `11,25`. These bypass the integer camera/dither-origin alignment, so check the final hosted/device rendering before adopting them. A browser preview does not establish physical e-ink quality.

## Development and verification

```sh
npm ci
python scripts/assets.py
python scripts/build_release_site.py
node scripts/build_framing_editor.mjs
python -m http.server 8890 --bind 127.0.0.1 --directory site
# Another terminal, with Chromium installed:
PLAYWRIGHT_EXECUTABLE_PATH=/usr/bin/chromium MAP_RELAY=true node scripts/check-framing-editor.mjs
```

Use `MAP_RELAY=true` only when the local asset relay is running, as described in the repository README. `FRAMING_ORIGIN` can select the published editor URL for a deployment check. The Pages workflow builds the editor automatically; no new backend service, credential or paid dependency is required.

[Browser preview](screenshots/framing-editor.png) shows only real geographic POIs. [Recorded browser checks](screenshots/results-framing-editor.json). Automated checks cover actual pointer dragging, OG/X isolation, portrait, all sixteen harbors, both fractional examples, native integer fitting, draft reload, shared-link import and an unchanged production registry. Unit checks reject unknown ports/devices, out-of-range coordinates and malformed drafts. Draft links contain only camera proposals, with no credentials or vessel records.

The builder copies the original framework, MapLibre and font licenses alongside the assets. Framework code is MIT, MapLibre is BSD-3-Clause, and the included TRMNL, Inter and Nico fonts use SIL OFL. Original copyright notices and full license texts remain in `framing/licenses/`; map data retains native OpenStreetMap attribution. No map tile archive is redistributed.
