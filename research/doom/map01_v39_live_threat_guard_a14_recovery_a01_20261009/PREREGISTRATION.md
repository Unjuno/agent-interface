# A14 preregistration — bounded recovery follow-up

Allocation: `map01-v39-live-threat-guard-a14-recovery-20261009`
Issue: #59
Source freeze: current `main` SHA `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`.
Owner/lane: this Codex task on the local Mac; one exclusive invocation in dedicated OrbStack VM `issue59-live-v39-a01-20261009`. Expiry is the first of the 12-decision cap, a terminal/runtime stop, or 600 seconds. The user explicitly directed a live run in this turn.
Model/input route: qualified first-party Codex app-server JSONL relay, `gpt-5.6-luna` at low effort; no manual input, no model prewarm, no relay response delay.
Fixture: `map01-threat-contact-v2`, seed `990624`, skill 1, MAP01, ViZDoom 1.3.0, frozen Freedoom WAD.

**H — Hypothesis.** A13 exposed two hard-health guards; one guard at the 10-decision boundary had no opportunity for the preregistered two-decision recovery check. With the unchanged V39 controller and a 12-decision cap, a guard at or before decision 10 can be followed by a fresh, non-discarded plan within two decisions. This allocation measures that follow-up opportunity, not causal survival benefit.

**T — Treatment.** Run the frozen controller once from the fixed fixture, seed 990624, `gpt-5.6-luna` low, at most 12 decisions. Do not delay or reissue responses. No manual gameplay or alternate action path. A guard later than decision 10 can remain right-censored.

**D — Decision and measurements.** Retain raw app-server protocol, events, typed observations, images, owner/release records, usage, score, stdout/stderr, and hashes. Independently classify every hard-health guard as fresh recovery within two decisions, observable miss after two available decisions, right-censored, or insufficient receipt. Also retain cancellation/release custody, stale-answer rejection, useful feedback during model intervals, ammo/progress, and terminal state. This one run does not close Issue #59 unless its other separate gates are met.

**C — Controls.** Freeze source, runtime closure, fixture, WAD, runner/auditor/tests, model/effort, seed, VM, resource checks, output path, and stop rules before launch. Require exact current-main identity and ancestry; exact guest mount and entrypoint hashes; Python 3.12.3, ViZDoom 1.3.0, Pillow 12.3.0, python-xlib 0.33, openpyxl 3.1.5; at least 2 GiB guest available memory and `/tmp`; no existing game/display process; and exact WAD hash. One invocation only. Stop at 12 decisions, death, MAP01 exit, runtime/model failure, or 600 seconds; the outer host relay has an independent 900-second hard limit for teardown. Preserve the first outcome; no retry, resume, or in-place repair.

**U — Uncertainty and scope.** A single episode is descriptive. A late guard without two later decisions is right-censored, not a recovery failure. Recovery does not establish useful feedback, task success, causal benefit, general reliability, physical key state, or game consumption. A13 and all earlier allocation outcomes remain unchanged.

Output: `results-local/doom/map01-v39-live-threat-guard-a14-recovery-20261009/`.
