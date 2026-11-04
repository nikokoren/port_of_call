# Major harbor collection: 13 data-verified areas from 15 candidates

The next collection prioritizes the US and Europe: **six European areas, six US areas and three Asian hubs**. This is a curated set of major, recognizable harbors, not a claim that these are the world's fifteen largest by tonnage or containers. The existing Finnish profile remains separate and usable. The [completed real-data check](coverage/README.md) found fresh reports in all six European areas, all six US areas and Singapore. Those 13 are data-verified in the registry; Shanghai/Yangshan and Busan New Port remain unverified after zero reports in this window. Public-display/cache rights remain a separate deployment gate.

| Region | Candidate area | Stable ID |
|---|---|---|
| Europe | Rotterdam | `rotterdam` |
| Europe | Antwerp | `antwerp` |
| Europe | Hamburg | `hamburg` |
| Europe | Bremerhaven | `bremerhaven` |
| Europe | Felixstowe / Harwich | `felixstowe` |
| Europe | Southampton | `southampton` |
| US | Los Angeles / Long Beach | `los-angeles-long-beach` |
| US | New York / New Jersey | `new-york-new-jersey` |
| US | Savannah | `savannah` |
| US | Houston Ship Channel | `houston` |
| US | Seattle — Elliott Bay | `seattle` |
| US | Charleston | `charleston` |
| Asia | Singapore | `singapore` |
| Asia | Shanghai — Yangshan | `shanghai-yangshan` |
| Asia | Busan New Port | `busan-new-port` |

The versioned registry stores candidate bounds, center, timezone and region. These are observation rectangles to review against real data and map tiles, not official port limits. Some entries cover shared harbor approaches. Yangshan and Busan New Port deliberately identify particular terminal areas; Seattle does not include Tacoma, and Houston's box covers the upper ship channel rather than the whole Galveston Bay. No UN/LOCODE identities or universal coverage are claimed. A single sample is evidence of observed coverage at that time, not a lasting guarantee.

## Private coverage check

The workflow `.github/workflows/aisstream-coverage.yml` reads the repository secret **`AISSTREAM_API`** into the probe's `AISSTREAM_API_KEY` variable on the GitHub runner. The value is never read back, put into an artifact, or sent to the plugin. A repository secret is available to Actions, not automatically to the cloud workspace or a deployed backend.

Use GitHub Actions → **AISStream coverage** → **Run workflow**, on `main`. Default: one 900-second compressed subscription covering all 15 areas, sent within two seconds. No per-MMSI filter is used, so the documented 200-MMSI filter limit does not cap the observed harbor traffic. The workflow permits 60–900 seconds and serializes its own coverage jobs. You can select a comma-separated subset of IDs. This is manual only; regular pushes do not open AIS connections.

```sh
gh workflow run aisstream-coverage.yml --ref main -f seconds=900
# A small first check instead:
gh workflow run aisstream-coverage.yml --ref main -f seconds=300 -f ports=hamburg,rotterdam,new-york-new-jersey
```

The same command can run locally when an API key has been provided securely to the process (never paste it in chat or commit it):

```sh
.venv/bin/python -m port_of_call.coverage --list
.venv/bin/python -m port_of_call.coverage --seconds 900 --output var/coverage.json
```

Reports contain **aggregate counts only**: distinct MMSIs observed over the window, report count, current positions under 60 minutes, positions under 30 minutes, names, valid headings/course, useful orientation/type completeness and latest observation time, per area. They contain no vessel identifiers, ship names, vessel coordinates or key. Subscription/compression confirmation, validation rejects and partial/blocked windows are recorded. A disconnected window is incomplete and must be rerun rather than called a completed test.

An unstarted or unauthenticated area is **unmeasured (`null`)**, not zero. Zero after a successful subscription means no reports were observed during that window, not no ships in port. Even a completed window is an event sample rather than a complete harbor inventory; repeated windows and a multi-hour run are needed before making reliability promises. The probe never updates `verified` or the live store.

The one-connection design follows previously observed AISStream documentation. **15 boxes is an application cap, not an asserted provider allowance.** Successful authentication/subscription must prove the selected set works for this account. Its documented account/IP connection caps still apply across other applications. Do not run this alongside three existing streams. Current website/terms requests returned 403 on the latest research attempt; earlier documentation evidence does not establish today's redistribution permission or prices.

## Promotion to a public recipe

1. Inspect real coverage reports for freshness, field completeness and gaps. Review the candidate map extents against genuine positions, especially large port complexes. Retain evidence and repeat any weak/empty sample.
2. Confirm current AISStream account terms explicitly allow the intended cache, public derivative display and distribution to community recipe users. Store the applicable terms/confirmation in the source evaluation notes. A key does not establish public redistribution rights.
3. Set `verified: true` only for areas with reviewed genuine coverage and map extents, referencing the evidence. This data-verification flag does not grant display rights: the deployed backend independently requires `AISSTREAM_RIGHTS_CONFIRMED=true`. Unverified entries are excluded from the public catalog, endpoints, production collector and packaging. The initial 13 entries now reference the completed coverage run.
4. Deploy one persistent collector/backend with `PROVIDER=aisstream`, its own `DB_PATH`, a securely provided `AISSTREAM_API_KEY` and `AISSTREAM_RIGHTS_CONFIRMED=true`. Do not enable the rights flag merely to skip a review. A backend with no verified harbors fails before subscribing.
5. Build the matching plugin form and import archive from the same verified catalog:

```sh
python scripts/package_recipe.py --provider aisstream --origin https://harbor.example.com
```

This writes `dist/port-of-call-aisstream.zip`; it does not overwrite the Finnish `settings.yml`. The current AISStream archive contains exactly the 13 data-verified areas. With no data-verified entries the command refuses to generate an archive. Building this private-test code package does not publish a service or approve community distribution. The normal `npm run package` still builds the verified Finnish profile. Each deployment serves one provider, preserving attribution and persistence boundaries.

Provider keys remain shared server infrastructure: ordinary recipe users choose a harbor and never provide their own AIS key. A single continuously connected subscription serves all installations, independent of screen refresh frequency. Do not substitute periodic brief GitHub Actions samples for the production collector; events have no guaranteed replay and Actions jobs are not durable services.

## Map-only frame review

All fifteen candidate extents were rendered through the real TRMNL vector tile source during preparation, with no vessel data and an explicit unverified-area label. These checks establish basic geographic framing, not AIS coverage. Reproduce with the ordinary preview assets/browser installed:

```sh
node scripts/harbor-frames.mjs
```

Output stays in ignored `var/major-frames/`; it is not a traffic snapshot. `MAP_RELAY=true` selects the existing TLS-verifying relay when required by the cloud runtime. Production stream writes are committed in batches about every five seconds so disk synchronization does not stall continuous message consumption. API reads on the same connection see the current reports and feed timestamp between commits.
