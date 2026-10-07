# Owner telemetry / post-sample cancellation composition A01

## H / T / D / C / U

- **H:** The #7429 telemetry-preserving `InputOwnerV12` reports an ordinary `release` if cancellation becomes visible after its dispatch-time cause sample but before the owner release is verified. Adding a cancellation recheck at the release-record boundary will preserve `cancelled` while retaining V11's ordinary key-up interval receipt.
- **T:** Freeze the #7429 owner V12 parent source and an additive successor with only the release-record cause recheck. Force the exact race with a fake Xlib queue hook and a synchronized cancellation thread. Compare parent, successor, and an uncancelled positive control; separately exercise the inherited explicit-up telemetry receipt.
- **D:** Parent forced-race receipt is `release`; successor forced-race receipt is `cancelled`; both verify empty key state and press/release ordering. Uncancelled cleanup remains `release`. Successor remains a V11 subclass and explicit `up` returns the existing interval telemetry schema.
- **C:** Deterministic software-thread/XTest fake boundary only. The cancellation setter is synchronized after dispatch cause sampling and before release verification; this is a forced schedule, not an estimate of natural race frequency.
- **U:** No physical X11 server, actual application, game, model, useful feedback, recovery, MAP01 outcome, or live allocation. No claim about hardware keyup time or task effect.

## Frozen sources and execution

- Parent: PR #7429 head `0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2`, `research/live_control/input_owner_v12.py`.
- Candidate: same source with one cancellation recheck immediately before constructing the verified owner-release record.
- The candidate runner obtains the parent bytes from the pinned Git commit object and exercises parent and candidate in fresh owner instances.
- Docker/OrbStack was checked before execution. If no pinned Python image can run because the local content store is unavailable, retain the environment STOP and run only the explicitly scoped host fake-Xlib construction; do not infer container validation.

## Result

`STOP_SETUP_IMPORT`: the frozen A01 runner failed before owner construction because `research/live_control` was missing from `sys.path`, so `input_owner_v11` could not be imported. No candidate case ran and no semantic outcome is claimed. Exact command and disposition are retained in `STOP.json`. The A02 successor has a separately frozen import wrapper and output directory; A01 remains immutable.
