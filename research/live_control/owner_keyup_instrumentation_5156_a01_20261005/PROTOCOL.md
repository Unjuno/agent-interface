# Issue #5156 — owner-thread per-key KeyRelease instrumentation A01

## H / T / D / C / U

**H.** Starting from the current-main `InputOwner` v10, recording a monotonic interval around each individual `XTest KeyRelease` request and its existing `XSync` completion will produce identity-bound key-up receipts nested within the existing caller-side release interval, without adding an X11 query or an `XSync` between keys in a bulk release. A sync failure must remain explicitly unknown and must not create a successful completion receipt.

**T.** One deterministic, source-bound WSLc construction run uses fake Xlib modules and the exact current-main V10 owner/wrapper as its baseline. It exercises a single explicit key-up, two ordered keys, cancellation-triggered bulk cleanup, explicit bulk release, and an injected XSync error. An independent raw-only auditor reconstructs the cases and rejects timestamp inversion, missing/duplicate receipts, identity changes, false verification, and a false successful-sync marker. No actual X server or OS input is opened.

**D.** `PASS_OWNER_KEYUP_INSTRUMENTATION_SCOPED` only if the candidate preserves the baseline XTest operation order and caller behavior in every case; each completed per-key record binds owner/token/key/reason and satisfies `caller_start <= owner_keyup_start <= owner_sync_return <= caller_return`; a bulk release retains one shared XSync after all per-key requests; failed XSync yields no completion time and no verified transition; cleanup leaves the fake keymap neutral; the independent audit reconstructs every raw row and rejects all frozen mutations. Any missing, duplicated, misbound, reordered, or falsely successful record is FAIL. The result is construction evidence only.

## Frozen sources and execution envelope

- Base: `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310`.
- `research/live_control/input_owner_v10.py`, Git blob `341b3c01649943ddaad5f28431a792c4889cc36e`.
- `research/live_control/input_transition_owner_v3.py`, Git blob `99dfc7c9907b018e7473bc2ba8a7393a5b221f51`.
- `research/doom/doom_retained_input_backend_v4.py`, Git blob `f0a9e2f40c14198b6be02dae8be904c8cac9c3d6`.
- WSLc image must be the locally inspected immutable `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, linux/amd64, Python 3.12.15). Pull is forbidden.
- One disposable CPU-only container at a time; network disabled; source mounted read-only; candidate and auditor each run at most once, sequentially; separate writable output directory; no retries. `--memory` is omitted because this host has reported unavailable cgroup/swap enforcement.
- Freeze candidate, fake-server, audit, and decision-rule source hashes before the one candidate invocation. If source/image identity or empty-container preflight fails, retain STOP and run nothing.

**C.** A no-error synthetic run could miss real Xlib/server errors or OS scheduling effects. Several keys in one batch share one XSync return, so the per-key intervals overlap in time and are not independent release latencies. XSync completion does not prove physical key-up, application consumption, or useful effect.

**U.** Fake-server source-contract behavior only. No X11 server, physical input, MAP01/game, model, GUI, task effect, release-latency distribution, safety rate, recovery benefit, host real-time scheduling guarantee, or production promotion is claimed. Formal X11 testing remains separately gated by Issue #5156 and the private lane/owner assignment; this construction does not grant it.
