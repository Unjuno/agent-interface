# V39 per-key batch query boundary A02

This package retains an algorithm-boundary experiment motivated by #59's per-key release measurement question. It is not an experiment on the active V39 runtime path.

## H / T / D / C / U

- **H:** With two owner-held keys, one pre-batch bitmap, ordered per-key UP injections, a successful sync, and one post-batch bitmap can produce one independently classified result per key while eliminating keymap queries between UP injections.
- **T:** On the archived V12 transition-classifier copy at `research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py`, compare sequential pre/UP/sync/post sampling with shared batch-boundary samples. Also fail the second UP injection. Candidate input was fixed to keycodes 65 and 74; the A02 candidate ran once.
- **D:** Both normal models must classify both keys `CONFIRMED_PHYSICAL_UP` and finish neutral. Batch mode must use two total keymap queries and none between UP injections. With the second injection failing, preserve the first confirmed UP and mark the second `RELEASE_UNCONFIRMED`. No input authority is granted.
- **C:** This uses the exact `_classify_release` function from the archived experiment source and a deterministic fake keymap. It models ordered events and a sync barrier but does not run Xlib, the V39 owner thread, its event queue, session startup, receipt publication, or external input.
- **U:** It establishes only that this classifier can consume shared before/after bitmaps in the simple model. The common interval does not establish per-key edge order or a tight per-key latency interval. No X server, OS input, V39 startup behavior, useful application effect, threat response, bounded recovery, or performance is tested.

## A02 result

The sequential control confirmed both keys with four total keymap queries and two between UP calls. The batch model confirmed both keys with two total keymap queries and zero between UP calls. When the second injection failed, the first key remained confirmed up and the second was `RELEASE_UNCONFIRMED`; the final modeled bitmap correctly retained keycode 74 as down. The independent audit passed.

A01's harness accounting failed after simulating its cases and before writing a result. Its freeze and failure receipt remain under `results/a01/`; A02 is a separate corrected run, not a rewritten A01 outcome.

## Current V39 source path audit

The pinned source audit corrects an easy but consequential source mix-up. The classifier snapshot used above is **not** the V12 module imported by current V39:

- The controller defaults to `session_map01_v12.py`; the `--measurement-session` option selects `session_map01_v15.py`.
- Default session V12 imports `doom_typed_release_backend_v1` and `executor_v12`; that backend replaces its owner with `input_owner_v10`.
- Opt-in session V15 binds `doom_owner_thread_release_batch_backend_v1` and `executor_v13`. The release-batch backend calls the transition owner once for each UP, then reconciles the owner state after the batch. Transition owner V4 imports `input_owner_v12` from the `research/live_control` search path established by session V12.
- That active `research/live_control/input_owner_v12.py` records per-key XTest KeyRelease/XSync receipts with `physical_verification_authoritative=False`. It has no `_classify_release` or per-key keymap sampler in its ordinary UP path. Its batch reconciliation checks the owner-held set, not an observed per-key physical key-up.

The active V39 path therefore has a missing per-key physical-up measurement. The two between-UP keymap queries seen in PR #7851's candidate composition came from substituting the archived sample-enabled owner; they are not queries made by current opt-in V39 source. `CURRENT_RUNTIME_SOURCE_LOCK.json` and `audit_current_runtime.py` pin and verify this source path and distinction.

## Next integration rung

Evaluate a batch-scoped physical sample around the actual opt-in V15 sequence: one owner-thread keymap sample before its ordered per-key UP/XSync receipts and one afterward, retaining per-key identity, context, and partial outcomes. First test it against the exact V39 opt-in startup closure with a fake X display. Any live use needs a separately frozen source/allocation and explicit resource assignment; none is implied by this package.

## Reproduction and evidence

The one-shot A02 candidate is consumed; do not rerun or replace `results/a02/RESULT.json`. Its byte-identical candidate source is retained for inspection only at `results/a02/archived_candidate_probe.py`; the package-root `probe.py` now fails closed before any experiment code can run. Read-only checks may be rerun:

```sh
python audit.py
python audit_experiment_source_binding.py
python audit_current_runtime.py
python audit_manifest.py
```

A02's original experiment base is `69dd261430cb1ed875f5a76411c4a2a54777c114`; the archived source blob is identical at delivery base `84d98a8eaf5763d45887478a40370d92f16e87ac`. The runtime path files are independently SHA-256 and Git-blob pinned to the delivery base.
