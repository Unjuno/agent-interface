# MAP01 V39 live threat guard A05

Allocation: `map01-v39-live-threat-guard-a05-20261009`
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
Source rule: exact current `main` and complete V39/V15 transitive runtime closure, frozen immediately before launch.
Runtime lane: dedicated OrbStack Ubuntu Noble arm64 VM `issue59-live-v39-a01-20261009`; Xvfb `1280x800x24`, no TCP listener.
Fixture: `map01-threat-contact-v2`, seed `990619`, skill 1, MAP01, ViZDoom `1.3.0`, Pillow `12.3.0`, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

## H/T/D/C/U

**H — Hypothesis.** The corrected current V39/V15 runtime can cancel the exact active cover when fresh typed health crosses its hard validity floor during a pending planner turn, discard the dependent answer, release inputs through the owner, and admit bounded recovery only from newer evidence. The independent progress scorer will measure useful task feedback during pending inference.

**T — Treatment.** One live episode with the fixed fixture, seed `990619`, model `gpt-5.6-luna` low effort, at most 10 decisions, and 600-second in-game timeout. This is a new allocation after A04's session-startup STOP. A05's sole instrumentation change is a wrapper in the portable entry that drains and retains the frozen session child stderr from process start; it does not change V39/V15 source or planner/input behavior. No prewarming, manual gameplay, alternate input, retry, or in-place repair.

**D — Decision.** Retain planner protocol, session stderr, controller events, exact guard/cancellation, per-key release and owner receipts, typed health/ammo, scorer-only events, score and terminal. PASS requires hard-health guard exposure during a pending model turn, matching cancellation and complete verified empty release, no stale answer, useful scorer event during inference, and fresh recovery within two later decisions. FAIL is a reproduced lease/cancellation error, missing custody, stale admission, or unverified release. HOLD is no required exposure/event/recovery. STOP preserves startup/model/runtime failure, death, MAP01 exit, or timeout, with no retry.

**C — Controls.** Preserve the A02/A03/A04 fixture, model, seed, controller, schema, and input contract. A03 stopped before Python controller import due missing Pillow. A04 fixed that dependency but its child session exited before `ready`; A04 artifacts record zero model turns and leave game-init state unknown. A05 preserves both earlier allocations unchanged and adds only startup stderr capture for diagnosis. Exact source hashes, wrapper, runner, auditor, fixture, WAD, CLI, VM, packages, output path, and stopping rule are frozen before launch.

**U — Uncertainty.** A single episode cannot establish generality, survival benefit, causality, or MAP01 completion. X11 key-up receipts do not prove physical key state or game consumption. An app-server thread start is not a model turn. Startup evidence is not threat-control evidence.

Unique output: `results-local/doom/map01-v39-live-threat-guard-a05-20261009/`. The launcher refuses existing output, dirty source, moved main, or source-closure mismatch. It verifies the pinned guest runtime, WAD, Xvfb, VM capacity/process state, and mount before writing `FREEZE.json` or starting app-server/game. A05 will run once only.
