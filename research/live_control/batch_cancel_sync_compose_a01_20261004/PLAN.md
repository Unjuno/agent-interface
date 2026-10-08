# Batch key-release interval + cancellation composition A01

## H / T / D / C / U

**H.** Starting from current-main `input_owner_v12.py` at `dae347cb83`, porting only the per-key request-start-to-common-XSync interval instrumentation from open PR #7504 will preserve the current-main cancellation recheck after batch sync. If cancellation becomes set by the XSync callback during an ordinary `release`, the record will be `cancelled`, verified empty, and will carry one interval per released key, without adding a sync per key. The existing explicit-up cancellation receipt will remain present.

**T.** Run two one-shot Fake-Xlib cases against a source-pinned derivative: (1) press W and A, then set cancel from the batch-release XSync callback; (2) press W, then set cancel from explicit-up XSync. Inspect exact event ordering, release sync count, cancellation classification, per-key bounds and explicit-up receipt. Run a separate raw/source auditor after the candidate exits.

**D.** `PASS_SYNTHETIC_COMPOSITION` only if the batch case has exactly one batch XSync, W/A press and release events in order, a verified empty `owner_release(reason=cancelled)`, two identity-ordered integer intervals each ending no later than `verified_ns`; and the explicit-up case retains `owner_explicit_keyup(cancel_requested_after_sync=true)`. Candidate exit and independent audit must both be zero. Any missing/malformed interval, ordinary classification, extra per-key sync, missing explicit-up cancellation receipt, or audit mismatch is FAIL. No retries.

**C.** Fake Xlib applies key state immediately at `fake_input()` and injects cancellation synchronously inside `sync()`. Thread scheduling, X server behavior, physical key transitions and application event consumption are deliberately outside this model. The ordinary release request begins before cancellation becomes visible, so the post-sync recheck is the discriminating source behavior.

**U.** This is host-side synthetic software construction because the local OrbStack Engine cannot read or lease content blobs (`operation not supported`). It does not establish timing accuracy, a real X11 release interval, live GUI/game effect, useful feedback, recovery, safety, performance or the #59 live gate. No X server, game, model, network, GPU or positive real input is used.

## Frozen source and environment

- Current-main base: `dae347cb8333f4469c89b076b0b466cc8bf6b960`.
- Exact owner source: `dependencies/input_owner_v12.py` (SHA-256 in `SOURCE_MANIFEST.json`).
- Instrumentation reference: #7504 head `65b29cf63efad1c66db58e2df29d533045304f03`, file `dependencies/input_owner_v13_reference.py`.
- Candidate: `candidate/input_owner_v12_composed.py`; it is current-main V12 plus the isolated batch interval hunk. No runtime or main file is changed.
- Runtime: macOS 27.0.1 arm64, CPython 3.14.5.
- Planned command: `python3 -B run_a01.py`.
- Docker diagnostics before freeze: OrbStack context/server reachable, but `docker image ls --digests` and `docker pull python:3.12-alpine` each failed reading/creating a containerd content blob with `operation not supported`. No daemon restart or cleanup was attempted.

The candidate was not run before this freeze. Runner/auditor source, source hashes, conditions and disposition gates are frozen by `FREEZE.json`.
