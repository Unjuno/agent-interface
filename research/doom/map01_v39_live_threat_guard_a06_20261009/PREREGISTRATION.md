# MAP01 V39 live threat guard A06

Allocation: `map01-v39-live-threat-guard-a06-20261009`
Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59)
Source rule: exact current `main` and complete V39/V15 transitive runtime closure, frozen immediately before launch.
Runtime lane: dedicated OrbStack Ubuntu Noble arm64 VM `issue59-live-v39-a01-20261009`; Xvfb `1280x800x24`, no TCP listener.
Fixture: `map01-threat-contact-v2`, seed `990619`, skill 1, MAP01, ViZDoom `1.3.0`, Pillow `12.3.0`, python-xlib `0.33`, Freedoom WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

## H/T/D/C/U

**H — Hypothesis.** The current V39/V15 runtime can cancel the exact active cover when fresh typed health crosses its hard validity floor during a pending planner turn, discard the dependent answer, release inputs through the owner, and admit bounded recovery only from newer evidence. The independent progress scorer will measure useful task feedback during pending inference.

**T — Treatment.** One live episode with the fixed fixture, seed `990619`, model `gpt-5.6-luna` low effort, at most 10 decisions, and a 600-second in-game timeout. A06 is a fresh allocation after A05's missing-Xlib startup STOP. It adds pinned `python-xlib==0.33` and a read-only import preflight for the complete V15 session module before any game/model start. The A05 stderr-capture wrapper remains. No prewarming, manual gameplay, alternate input, retry, or in-place repair.

**D — Decision.** Retain planner protocol, session stderr, controller events, guard/cancellation, per-key release and owner receipts, typed health/ammo, scorer-only events, score and terminal. PASS requires hard-health guard exposure during a pending model turn, matching cancellation and complete verified empty release, no stale answer, useful scorer event during inference, and fresh recovery within two later decisions. FAIL is a reproduced lease/cancellation error, missing custody, stale admission, or unverified release. HOLD is no required exposure/event/recovery. STOP preserves startup/model/runtime failure, death, MAP01 exit, or timeout, with no retry.

**C — Controls.** Keep the A02-A05 fixture, seed, model, controller, schema, and input contract. A03 lacked Pillow; A04 then failed before ready; A05 stderr revealed missing Xlib through session_v9. A06 preserves those first outcomes and changes only the disposable VM dependency closure by adding pinned python-xlib, plus import-only verification and retained child stderr. The frozen controller/runtime source remains exact main. Freeze all source/harness hashes and runtime identities before starting the app-server or game.

**U — Uncertainty.** A single episode cannot establish generality, survival benefit, causality, or MAP01 completion. X11 key-up receipts do not prove physical key state or game consumption. An app-server thread start is not a model turn. Import preflight is not gameplay evidence.

Unique output: `results-local/doom/map01-v39-live-threat-guard-a06-20261009/`. The launcher refuses reused output, dirty source, moved main, or source-closure mismatch. It verifies pinned packages, full V15 imports, WAD, Xvfb, VM capacity/process state, and mount before freezing and launching. A06 runs once only.
