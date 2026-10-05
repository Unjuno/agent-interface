# Current-owner A03: pending expiry receipt across execute exit

## H / T / D / C / U

**H.** The latest PR #7805 InputOwner v13 candidate still leaves the owner-release record pending after the bridge's `execute()` final drain when cleanup is blocked after its per-key `sync()`. A V3 measurement bridge that drains in `release_all()`'s `finally` will publish the resulting context/actuation-bound physical-up receipt before ExecutorV12 emits its expired terminal.

**T.** Freeze main `dccf55e264f434ca27f2948fe53be09919047819`, PR #7805 head `c4e893e8515811c77e21639237f1f2a914d4d88b`, bridge candidate blob `ee1220cdc3d93d96aa1051c072ca7dceeb59c35d`, and current InputOwner v13 blob `123cd29146e5cf9bfd96f4a749c5d421e34ec1e9`. On the existing fake-Xlib harness admit one F8 down, pause the expiry thread at its second `sync()` after the fake physical up but before `owner_release` record publication, allow `execute()`'s drain to finish, then observe ExecutorV12 enter its `release_all()` path and release the gate. Invoke the formal candidate once; audit only its saved JSON.

**D.** Scoped PASS requires one matching down and exactly one owner-confirmed per-key up with same program/step/intent/actuation identities; no owner record and cursor still zero at the execute-exit boundary; exactly one matching bridge `input_release_measurement` emitted before one `expired` terminal; owner verified empty before terminal; and empty final fake/bridge-held state. Otherwise retain the first outcome as FAIL/HOLD, with no rerun.

**C.** This is a forced schedule with a fake display. `release_all()` test seam mirrors pinned `session_v5.Backend.release_all` (`owner.call('release', lease)`, then clear held). One deterministic interleaving cannot estimate event frequency or live X11 behavior.

**U.** No physical desktop, real X11, ViZDoom/game, model, independently useful feedback, bounded recovery, threat-control, task effect, latency, MAP01 progress, production readiness, or Issue #59 completion is tested. The full candidate owner is from an open PR and is identified by its exact frozen Git blob, not asserted to be merged/runtime code.

## Execution discipline

Preflight imports a fake owner and sends no key events. A03 was a container-construction STOP before candidate execution and wrote no candidate JSON under `results/formal_01/`. A04 is the sole scientific candidate invocation, with a write-once output under `results/formal_02/`; its auditor reads retained JSON only. Container is the immutable previously validated `python:3.12.11-slim` image digest `sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f`, `linux/arm64`, network disabled, repository source read-only, and only the corresponding result directory writable. No image pull or shared GPU use is requested.

## A03 construction STOP and A04 fresh run

A03 invoked the container but failed before candidate execution because the package-only mount contradicted `HERE.parents[2]`'s repository-root assumption. The exact stderr and command are retained in `STOP_A03.txt`; A03 candidate executions=0 and is not retried. A04 is a new write-once run ID with no scientific/source change: it mounts the repository at `/workspace`, keeps the package source read-only, mounts only `results/formal_02/` writable, and runs the same frozen hypothesis against the same candidate head/source blobs. Its runner/audit/output paths are distinct. A04 ran once and passed its scoped audit; preserve its raw output and do not rerun it.
