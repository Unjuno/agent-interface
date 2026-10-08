# MAP01 V39 live threat guard A04

Allocation: `map01-v39-live-threat-guard-a04-20261009`
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
Source rule: exact current `main` and complete V39/V15 transitive runtime closure, frozen immediately before launch.
Runtime lane: dedicated OrbStack Ubuntu Noble arm64 VM `issue59-live-v39-a01-20261009`; Xvfb display `1280x800x24`, no TCP listener.
Fixture: `map01-threat-contact-v2`, seed `990619`, skill 1, MAP01, ViZDoom `1.3.0`, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

## H/T/D/C/U

**H — Hypothesis.** With PR #8691's lease-safe delayed-UP cancellation and terminal custody propagation integrated, the current V39/V15 runtime can cancel the exact active cover when a fresh typed health observation crosses that cover's hard validity floor while a slow planner turn is pending. It will discard the dependent answer, release the cover's inputs through the owner, and accept a bounded recovery plan only from a newer observation. The independent progress scorer will establish whether useful task feedback occurs while inference is pending.

**T — Treatment.** Execute one live episode on the fixed threat-contact fixture with `gpt-5.6-luna` at low effort, game seed `990619`, at most 10 planner decisions, and the existing 600-second in-game timeout. The 10-decision cap leaves room for guard exposure and at most two later recovery decisions. Use the first-party host Codex app-server through the frozen host/VM JSONL relay. No prewarming, manual gameplay, alternate input path, retry, or in-place repair.

**D — Decision and measurements.** Retain model requests/responses and usage, controller events, policy and running-action invalidation receipts, typed health/ammo observations and paired RGB artifacts, per-key release-batch deliveries and owner-thread key-up receipts, independent scorer samples/events, score, terminal, host/guest output, and hashes. A hard-guard exposure requires `health:below_hard_minimum` invalidation from a fresh typed pair while a model turn is pending. Correct cancellation requires a matched cover ID and intent token, dependent planner answer ineligible/discarded, no stale plan admission, X11 owner key-up evidence followed by verified empty release and terminal closure. A useful-feedback event is a scorer-only `KILL_COUNT_INCREASE` or `MAP_EXIT`; report its first timestamp relative to each pending model interval. Bounded recovery requires a plan admitted from a typed observation sequence newer than the invalidation within at most two later planner decisions.

**PASS** requires hard-guard exposure, matching cancellation, complete per-key/empty release, no stale answer, useful feedback during pending inference, and bounded fresh recovery. **FAIL** is a reproduced cancellation/lease error, missing or mismatched release custody, stale answer admitted after invalidation, or unverified final release. **HOLD** means the fixed episode ends without guard exposure, enough fresh recovery decisions, or an independent useful event during pending inference. **STOP** preserves the first runtime/model failure, death, MAP01 exit, timeout, or other terminal outcome without retry.

**C — Controls.** Keep the fixture, seed, model, effort, map, skill, V39 controller, schema, host relay, and input restrictions fixed. A04 is a fresh allocation after A03's pre-game STOP. Its sole environmental correction is to explicitly include Pillow `12.3.0`, required by the frozen V39 controller's `PIL` import, alongside ViZDoom `1.3.0`. A03 remains immutable and is not retried. Freeze all transitive runtime source hashes, runner, auditor, fixture input, WAD, CLI binary/version, VM identity, package versions, display command, output path, and stop rule before starting the model or game.

**U — Uncertainty and scope.** One episode is descriptive and cannot establish a rate, survival benefit, causal advantage, or MAP01 completion. Typed HUD evidence is not a general enemy detector. X11 key-up receipts establish server-side event processing and observed server state, not hardware key state or game consumption. Scorer progress is not proof the model action was correct.

## Stop, custody, and setup

Unique output directory: `results-local/doom/map01-v39-live-threat-guard-a04-20261009/`. The runner refuses reuse, a dirty experiment tree, stale main, or any runtime dependency differing from exact current main. Before starting app-server or guest it verifies the VM, pinned Python packages including Pillow, ViZDoom import and WAD digest, Xvfb, memory/disk, and no pre-existing game/display process. All local-image files require guest path receipts and matching host SHA-256 before forwarding. Preserve partial files and the first result even on failure. A03's distinct STOP and artifacts remain unchanged.
