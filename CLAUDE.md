# CLAUDE.md

Guidance for Claude Code (or any agent) working in this repository.

## What this repo is

`growatt_server_upstream` is a **HACS custom-component distribution** of an
enhanced Growatt Server integration for Home Assistant. It started as a copy
of `home-assistant/core`'s `homeassistant/components/growatt_server/`
directory and has since diverged significantly with real feature work never
contributed upstream: SPH sensor support (`sensor/sph.py`), a persistent
API-rate-limit guard (`throttle.py`), and various fixes. It has its **own
independent git history** — it is not a fork of `home-assistant/core` and
shares no commit ancestry with it.

Domain: `growatt_server` (same as core — remove HA's built-in integration
before installing this one, per the README).

## Related repos

- **`../core`** — the user's fork of `home-assistant/core`
  (`origin` = `johanzander/core`, `upstream` = `home-assistant/core`). Used
  as the source of truth for "what does current upstream core actually
  look like" when refreshing `vendor-sync` (see below). Its local `dev`
  branch can be very stale — always `git fetch upstream dev` there before
  trusting it as current.
- **`../PyPi_GrowattServer`** — the `growattServer` Python library this
  integration depends on (`manifest.json`'s `requirements`). The user is a
  contributor there too; library-level fixes (e.g. surfacing API error
  codes, client-side rate-limit handling) belong in that repo, not here.
  See its issues/PRs for in-flight work relevant to this integration
  (e.g. indykoning/PyPi_GrowattServer#154, #155, #156).
- **`bess-manager`** — a Home Assistant add-on that is a *consumer* of this
  integration's sensors/services (battery scheduling). Debugging a
  bess-manager report often traces back here or into `growattServer`.

## Branch strategy: vendor-sync vs master

Two branches, two different jobs. Do not blend them.

- **`vendor-sync`** — a pure, unmodified snapshot of
  `homeassistant/components/growatt_server` copied from current
  `home-assistant/core` upstream. **No local patches ever land here.** Its
  only purpose is to be a clean, up-to-date reference point:
  - to diff `master`'s accumulated changes against, so "what's ours vs
    what's upstream's" stays answerable at any time
  - as a clean base for testing whether a new fix/idea reproduces against
    vanilla core before deciding it needs a patch here
  - as the source of truth when eventually preparing an upstream
    contribution PR to `home-assistant/core`

- **`master`** — what HACS actually ships. `vendor-sync` plus every local
  patch (SPH sensors, throttle guard, growattServer version bumps, bug
  fixes), each as its own identifiable commit on top.

### Refreshing `vendor-sync`

```bash
cd ../core
git fetch upstream dev          # local `dev` branch is often stale — don't trust it un-fetched
git log -1 upstream/dev         # note the SHA, it goes in the sync commit message

cd ../growatt_server_upstream
git checkout vendor-sync
rm -rf custom_components/growatt_server
cp -r ../core/homeassistant/components/growatt_server custom_components/growatt_server
find custom_components/growatt_server -name "__pycache__" -exec rm -rf {} +
git add -A
git commit -m "vendor: sync growatt_server from home-assistant/core@<sha> (<date>)"
git push
```

Then decide per-change whether to merge/rebase the new upstream delta into
`master` (conflicts here are exactly the interesting part — they show where
our patches touch code upstream has since changed).

### Adding a new local patch

Commit it on `master` only, as its own commit with a clear message
describing *why* (not just what — the diff already shows what). If the
patch is something upstream would plausibly want, say so in the commit
message; that's the trigger for eventually splitting it into an upstream
PR against `home-assistant/core`.

## Testing changes locally

- `pytest tests/` runs the existing suite (config flow, init, sensors,
  number, switch, services, throttle).
- To test against a locally-edited `growattServer` (from
  `../PyPi_GrowattServer`) before it's released: install it editable into
  whatever Python env runs your test HA instance
  (`pip install -e ../PyPi_GrowattServer`), which satisfies the import
  regardless of the `manifest.json` version pin. Bump the pin for real once
  a release is cut.
- For end-to-end testing against a real Home Assistant instance, see
  `bess-manager`'s `docs/agents/` for how the user's dev HA instance and
  mock-HA e2e stack are reached — this repo doesn't have its own e2e setup.

## Rules carried over from bess-manager work

These apply here too, since the same user/workflow conventions hold:

- Never commit directly to `master` for anything beyond what's described
  above (vendor syncs and patches both go on `master` intentionally here —
  this repo has no separate release/beta branch split like bess-manager).
  For genuinely new/risky feature work, use a `feature/*` or `fix/*` branch
  and a PR, same as the existing branch history shows
  (`fix/sph-type5-device-list`, `feature/sph-sensors`, etc.).
- Never push to a remote or open a PR without the user's explicit go-ahead.
- Verify against actual source (upstream core, the growattServer library,
  real API responses/logs) before proposing a fix — don't guess at entity
  names, error codes, or upstream behavior.
