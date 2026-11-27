# MAP01 V39 live threat-guard A09

Allocation: `map01-v39-live-threat-guard-a09-20261009`
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
Source rule: exact current `main` and complete V39/V15 transitive runtime closure, frozen immediately before launch.
Runtime lane: dedicated OrbStack Ubuntu Noble arm64 VM `issue59-live-v39-a01-20261009`; Xvfb display `1280x800x24`, no TCP listener.
Fixture: `map01-threat-contact-v2`, seed `990620`, skill 1, MAP01, ViZDoom `1.3.0`, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

## H/T/D/C/U

**H — Hypothesis.** A07 reached ten decisions at seed `990619` without a hard-health guard or useful scorer event. Changing only the episode seed to `990620` may produce a distinct threat/health trajectory that exposes whether current V39/V15 cancels an active cover when fresh typed health crosses its hard validity floor during pending inference. If exposed, the runtime must discard the dependent answer, publish owner-thread input release, and admit recovery only from a newer observation.

**T — Treatment.** Execute one fresh live episode using the fixed threat-contact fixture with `gpt-5.6-luna` at low effort, seed `990620`, at most 10 planner decisions, and the existing 600-second timeout. Keep the first-party host Codex app-server relay and input path unchanged. The only treatment delta from A07 is the seed; A08’s 32-decision extension at seed `990619` remains a separate predecessor. No retry, manual gameplay, prewarming, or in-place repair.

**D — Decision and measurements.** Retain requests/responses and usage, controller events, policy/running-action invalidation receipts, typed health/ammo observations and paired RGB artifacts, per-key release-batch deliveries and owner-thread key-up receipts, independent scorer samples/events, score, terminal, host/guest output, and hashes. PASS requires hard-guard exposure during pending inference, matching cancellation, complete per-key/empty release, no stale answer, useful feedback during a pending interval, and bounded recovery from a newer typed observation within two later decisions. FAIL is a reproduced cancellation/lease error, missing/mismatched release custody, stale admission after invalidation, or unverified final release. HOLD means the episode completes without exposing the full gate. STOP preserves the first runtime/model failure, death, MAP01 exit, timeout, or other terminal outcome without retry.

**C — Controls.** Keep fixture, model, effort, map, skill, V39 controller, schema, host relay, input restrictions, and ten-decision cap fixed versus A07. Change only seed `990619` → `990620`. Freeze exact current-main SHA, complete runtime closure, harness, fixture, WAD, CLI binary/version, VM mount mapping, package versions, output path, and stop rule before starting app-server or game. A03-A08 remain immutable and are not retried.

**U — Uncertainty and scope.** A single seed is descriptive and cannot establish an effect rate, survival benefit, causal advantage, or MAP01 completion. The fixture may constrain how much the seed changes the saved world’s RNG trajectory. Typed HUD evidence is not a general enemy detector. X11 release receipts establish server-side event processing and observed server state, not hardware key state or game consumption.

## Stop, custody, and setup

Unique output directory: `results-local/doom/map01-v39-live-threat-guard-a09-20261009/`. The host runner requires the expected host checkout to map to the configured guest source root, verifies the OrbStack mount declaration, current-main identity/ancestry, all 54 runtime-source hashes, fixture/WAD hashes, Pillow, ViZDoom, `python-xlib==0.33`, `openpyxl==3.1.5`, Xvfb, memory/disk, and absence of pre-existing game/display processes before freezing or starting app-server/game. Every local image must have a guest receipt and matching host SHA-256 before forwarding. Preserve the first output even on failure.
