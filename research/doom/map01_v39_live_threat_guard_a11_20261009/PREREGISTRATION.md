# MAP01 V39 live threat-guard A11

Allocation: `map01-v39-live-threat-guard-a11-20261009`
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
Source rule: exact current `main` and complete V39/V15 transitive runtime closure, frozen immediately before launch.
Runtime lane: dedicated OrbStack Ubuntu Noble arm64 VM `issue59-live-v39-a01-20261009`.
Fixture: `map01-threat-contact-v2`, seed `990622`, skill 1, MAP01, ViZDoom `1.3.0`, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

## H/T/D/C/U

**H — Hypothesis.** A08 (seed 990619, 32 decisions) exposed neither a hard-health guard nor useful scorer feedback during pending inference. A09 (seed 990620, 10 decisions) exposed a hard-health guard during pending inference but no useful scorer event during pending inference. A10 (seed 990621, 32-decision cap) stopped after 13 decisions at death without exposing either gate condition; its one kill was outside pending inference. A11 is one predeclared independent episode at the next sequential seed, 990622, to determine whether the same frozen V39 path exposes the joint guard/feedback/recovery gate in that episode. This is descriptive replication; it does not estimate a causal seed effect or event rate.

**T — Treatment.** Run exactly one episode on the same fixed threat-contact fixture with `gpt-5.6-luna` at low effort, seed `990622`, at most 32 planner decisions, and the existing 600-second timeout. Keep the controller, schema, model, effort, host relay, input path, source closure, fixture, and other environment settings identical to A10. Use the dedicated Issue #59 VM only after live checks show no game/controller/Xvfb process and at least 2 GiB available memory and `/tmp` disk. A11 receives its own source checkout and output directory. No retry, manual gameplay, prewarming, or in-place repair.

**D — Decision and measurements.** Retain requests/responses and usage, controller events, policy/running-action invalidation receipts, typed health/ammo observations and paired RGB artifacts, per-key release-batch deliveries and owner-thread key-up receipts, independent scorer samples/events, score, terminal, host/guest output, and hashes. PASS requires a hard-health guard during pending inference, matching cancellation, complete per-key/empty release, no stale answer, useful scorer feedback during a pending interval, and bounded recovery from a newer typed observation within two later decisions. FAIL is a reproduced cancellation/lease error, missing/mismatched release custody, stale admission after invalidation, or unverified final release. HOLD means the episode finishes without the full gate. STOP records the first death, MAP01 exit, timeout, runtime/model failure, or other terminal outcome without retry. These labels apply only to this allocation; a STOP does not stop unrelated authorized work.

**C — Controls.** A11 changes only the fixture seed from A10's 990621 to the next sequential value, 990622. It retains the same 32-decision cap and all other settings. A08–A10 remain immutable, and the sequential sample is not a matched causal comparison. Freeze exact current-main SHA, complete runtime closure, harness, fixture/WAD, CLI binary/version, VM mount mapping, package versions, output path, and stop rule before starting app-server or game.

**U — Uncertainty and scope.** One episode is descriptive. It cannot establish an event rate, survival benefit, causal advantage, or MAP01 completion from a guard alone. Typed HUD evidence is not a general enemy detector. X11 release receipts establish server-side event processing and observed server state, not hardware key state or game consumption.

## Stop, custody, and setup

Unique output directory: `results-local/doom/map01-v39-live-threat-guard-a11-20261009/`. The host runner requires the expected host checkout to map to the configured guest source root, verifies the OrbStack mount declaration, current-main SHA/ancestry/runtime closure, fixture/WAD hashes, Pillow, ViZDoom, `python-xlib==0.33`, `openpyxl==3.1.5`, Xvfb, memory/disk, and absence of pre-existing game/display processes before freezing or starting app-server/game. Every local image must have a guest receipt and matching host SHA-256 before forwarding. The preregistered allocation is never rerun.
