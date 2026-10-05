# Owner telemetry / post-sample cancellation composition A02

## H / T / D / C / U

- **H:** The #7429 telemetry-preserving `InputOwnerV12` reports `release` when cancellation is set after the dispatch-time cause sample but before X11 release verification. A recheck at the record boundary should classify that cleanup as `cancelled` and preserve the inherited V11 explicit-up interval receipt.
- **T:** Against parent commit `0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2`, run one synchronized fake-Xlib schedule on both parent and the additive candidate, plus an uncancelled candidate control and explicit-up telemetry exercise. Do not repeat A01's setup STOP.
- **D:** Parent forced schedule says `release`; candidate says `cancelled`; both release the fake key and verify empty state. Candidate ordinary release remains `release`; V11 telemetry still reports `input_release_rpc` with a valid interval and no authority grant.
- **C:** Deterministic software schedule only; it does not measure natural race frequency. The fake Xlib state proves only the exercised test fixture's event ordering and empty set.
- **U:** No physical X11, application, game, model, useful feedback, bounded recovery, MAP01 result, or live allocation.

## Provenance / prior STOP

- Parent source SHA-256: `09cc23e67e6a3de1b0029fbb0184cdf54d3d8e29561281870d2b0b76027511d8`.
- Candidate source SHA-256: `f46dd62edd085afe29fe031f74a31397bb568f583affde0a26ac79686625d433`.
- A01's frozen pre-candidate `ModuleNotFoundError` is preserved in the sibling `map01-v39-owner-telemetry-cancel-cause-a01-20261004/STOP.json`; A02 changes only runner import setup and output path.
- Container preflight: `docker image inspect python:3.14` returned `No such image`. No image was pulled or built. This is host-only fake-Xlib construction, not a container result.

## Result

**A02 PASS (host-only construction).** The exact forced post-sample schedule made the #7429 parent classify cleanup as ordinary `release`; the successor classified it `cancelled`. Both produced fake KeyPress/KeyRelease in order and a verified empty key/button state. The successor's uncancelled control remained `release`. Its explicit key-up still emitted `input_release_rpc`, a nonnegative interval, the original intent token, and `grants_input_authority=false`; the class still directly extends `input_owner_v11.InputOwner`.

The candidate was run once with `python3 -B research/doom/results/map01-v39-owner-telemetry-cancel-cause-a02-20261004/run_candidate.py`. The independent saved-record auditor passed 24 checks. Applicable ExecutorV12/V13 tests passed 6/6 and `git diff --check` passed. Parent and candidate forced schedules are deterministic software interleavings; the experiment does not estimate race frequency or prove any live-control outcome.

The macOS OrbStack preflight could not run a container because `python:3.14` is absent locally. No pull/build was attempted. The A01 setup STOP remains unchanged. No game, model, X server, physical input, GUI, recovery episode, or formal allocation was used.
