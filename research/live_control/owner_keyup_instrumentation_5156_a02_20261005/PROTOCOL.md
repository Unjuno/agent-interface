# Issue #5156 — owner-thread per-key KeyRelease instrumentation A02

## H / T / D / C / U

**H.** Starting from current-main InputOwner v10, recording a monotonic interval around each individual XTest KeyRelease and its existing XSync completion produces identity-bound per-key receipts inside caller-side release brackets, without an extra X11 query or an XSync between bulk keys. A failed sync remains unknown and cannot be represented as successful.

**T.** This is a fresh successor to the failed A01 audit rung. One deterministic WSLc fake-Xlib construction run covers one explicit up, two ordered explicit ups, explicit two-key bulk release, cancellation cleanup, and an injected XSync failure followed by neutral cleanup. A separately invoked raw-result auditor checks exact baseline XTest/XSync order, owner/token/key/reason identity, timestamp nesting, shared bulk sync, neutral verification, authority limits, and eight frozen corruption controls. A01's raw result and FAIL remain historical and are not rerun or reclassified.

**D.** `PASS_OWNER_KEYUP_INSTRUMENTATION_SCOPED` only if candidate exit is 0, all five cases reconstruct, each completed key receipt matches its case owner/token/keycode/reason and has `caller_start <= owner_keyup_start <= owner_sync_return <= caller_return` for explicit ups, bulk keys share the same post-request sync timestamp and batch ID, all XTest/XSync call sequences match the baseline contract, failed sync has null completion time and false completion, every case ends with a verified neutral fake keymap, no row grants physical verification or input authority, and all eight mutations are rejected. Otherwise FAIL/STOP. This is source-contract construction evidence only.

## Frozen sources and execution envelope

- Base commit: `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310`.
- Baseline Git blobs: InputOwner v10 `341b3c01649943ddaad5f28431a792c4889cc36e`; transition wrapper v3 `99dfc7c9907b018e7473bc2ba8a7393a5b221f51`; retained backend v4 `f0a9e2f40c14198b6be02dae8be904c8cac9c3d6`.
- Candidate, fake-Xlib, runner, auditor, protocol, and baseline-copy hashes are fixed in `FREEZE.json`; the frozen package is committed before execution.
- WSLc image: cached immutable `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15. Pull forbidden.
- Candidate once, then auditor once only after candidate exit 0; each in a disposable CPU-only container with network disabled, read-only source, separate writable output. No retries. Memory limit omitted because cgroup/swap enforcement is unavailable on this host.
- A01 recorded a FAIL because its frozen auditor compared bulk releases to an earlier key-down sync and assigned the injected cleanup sync the wrong ordinal. A02 corrects those two checks and adds explicit owner-ID/keycode checks. This new protocol is not a rerun of A01.

**C.** Fake Xlib cannot model server errors, OS scheduling, focus changes, real event queues, or application consumption. Keys in a bulk batch share one XSync completion and are not independent latency observations. XSync is not proof of physical key-up.

**U.** No real X server, physical input, GUI, MAP01/game, model, useful task effect, recovery benefit, latency distribution, release-safety rate, real-time guarantee, or production promotion is claimed. Formal X11 testing remains separately gated by Issue #5156 and private lane/owner assignment; A02 does not grant that authority.
