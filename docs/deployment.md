# Deployment and private-plugin test

No public backend or TRMNL plugin was deployed during implementation: hosting/DNS and TRMNL account access were not supplied. You can test the Python API now without credentials. To complete end-to-end testing, provide a Linux host with persistent disk and a public HTTPS hostname, then perform the plugin import in your account.

## One small Linux VM

Use Python 3.12+, durable disk, one process and normal outbound HTTPS to `meri.digitraffic.fi`. Ubuntu 24.04 is a suitable base. A 512 MB–1 GB VM should be sufficient for modest adoption; measure actual memory/bandwidth before promising a capacity. No GPU, Docker, Redis, Worker or background browser is needed on the host.

As an administrator, create a system user `portofcall` and place the checkout at `/opt/port-of-call`, owned/readable by that user. Install a virtual environment:

```sh
cd /opt/port-of-call
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps .
```

Create `/etc/port-of-call.env` with non-secret defaults (mode 0600 if adding secrets later):

```ini
PROVIDER=digitraffic
HOST=127.0.0.1
PORT=8080
FRESH_SECONDS=1800
EXPIRE_SECONDS=3600
POLL_SECONDS=300
```

Copy `deploy/port-of-call.service` to `/etc/systemd/system/`, then:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now port-of-call
sudo journalctl -u port-of-call -n 30
curl -f http://127.0.0.1:8080/health
```

The service creates/writes `/var/lib/port-of-call/positions.sqlite3`; application files remain read-only. Give the host a public DNS name and use Caddy or your existing TLS reverse proxy. The example `deploy/Caddyfile` needs your real hostname. Only expose HTTPS; keep port 8080 on loopback. Configure a CDN/edge cache and rate limit for a large public recipe. The built-in limiter counts reverse-proxy traffic together intentionally; it does not trust client-supplied forwarding headers.

Test each endpoint through HTTPS. Then set the recipe polling origin and follow the README private-plugin steps. Required renderer destinations are `trmnl.com` (framework/MapLibre assets), `maps.trmnl.com` (native vector tiles), and your API hostname. Do not remove attribution or disable TLS verification to make a preview pass.

## Operation and upgrades

- Health is 200 only while last upstream success is within the expiry window, otherwise 503. Alert on repeated failures and sparse/old reports, not merely an open port.
- Log counters include validation rejects (often expired reports in a whole-country snapshot), accepted in-catalog reports and latest age per harbor. Track rate/response volume and disk.
- Restart preserves recent observations; it cannot resurrect expired ones. SQLite uses WAL. Back up with SQLite's online backup API or stop the service before copying all database state.
- Upgrade dependencies consciously, rerun tests and restart. Keep the same persistent database for the same provider. Use a separate database when switching providers.
- Run only one collector replica; default HTTP and collector share a process. No per-user stream subscription.
- No browser/fixture/preview server belongs in production. Leave `ENABLE_DEMO` unset/false.

For AISStream, run the private coverage workflow and promotion steps in [major-ports.md](major-ports.md). The repository secret `AISSTREAM_API` is used only on its Actions runner; the deployed service needs its own securely supplied binding. Confirm caching/public-display rights and promote reviewed registry entries before starting the production service. Supply `PROVIDER=aisstream`, `AISSTREAM_API_KEY` securely and `AISSTREAM_RIGHTS_CONFIRMED=true` **only after approval**, with a different `DB_PATH`. WSS access to `stream.aisstream.io` is needed. Verify the stream over a useful collection window before adding any candidate to public recipe settings. The production collector excludes unverified entries; no verified AISStream ports means startup fails before creating a subscription. Private coverage testing uses the separate probe.

## Troubleshooting

- HTTP 406 from Digitraffic: preserve `Accept-Encoding: gzip`; the implemented client decompresses automatically.
- Empty map: check `status`, viewport, latest observation and fresh/expiry thresholds. "No reports" is not proof of no ships. Wait for a successful poll; check the source's area coverage.
- Blank base map: check native JS/CSS and tile host access. The recipe displays a diagnostic on load failure. Canonical asset URLs were blocked from this cloud's research client, so production renderer access remains a private-test check.
- Names missing: static metadata may not be known or may be expired; valid positions still render. Names are optional in every layout, with smaller label budgets in compact views. A name is omitted if it would cover a ship, the information box, another name or attribution. Leader lines can place a name farther from its ship without moving the ship.
- Too few markers: compare `total`, `shown`, `omitted` and the screen's decluttering notice; try Closer framing. Markers are never displaced to make room.
- 429: use the cached endpoint/edge cache and do not forward untrusted IP headers. Standard refresh is 15 minutes, not one backend poll per device.
