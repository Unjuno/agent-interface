# C03 — post-sample cancellation cause boundary

## Result

`PASS_C03_POST_SAMPLE_CANCEL_BOUNDARY_REPRODUCED` means the predicted residual counterexample was reproduced; it is not a PASS for the v12 repair. After the v12 owner sampled `cancel.is_set() == False`, a separate Python thread made cancellation visible before the owner invoked release. The owner still recorded `reason=release`. The retained current-main v10 comparison likewise recorded `release` when cancellation arrived after dequeue, and the uncancelled v12 positive control correctly stayed `release`.

All three cases emitted exactly one fake KeyPress and one fake KeyRelease for keycode 38, returned a verified owner receipt with no keys down, and settled the cancellation setter thread. The independent auditor passed all 18 checks. The frozen v10 source is byte-identical in the later current-main snapshot `89a3dfc12edfd2e17eb94c4743599cbb158e5a5b`; the frozen v12 source is byte-identical at the later PR #7440 head `1eadd189debbed2014a92ad813d4413c44f22873`.

## H / T / D / C / U

- **H:** If cancellation becomes visible after the owner has sampled the cancellation flag false for release-cause selection, but before the first key-up side effect, additive v12 may still record ordinary `release`.
- **T:** One deterministic fake-Xlib owner-thread cycle per exact source: current-main v10 with cancellation after dequeue; PR #7440 v12 with a separate thread synchronized to set cancellation just after its false cause sample; and a v12 ordinary-release positive control.
- **D:** The counterexample is reproduced only when each cycle has one fake press/release and a verified empty owner receipt; v10 and v12-cancel both record `release`; v12 timestamps satisfy sample-false < cancellation-visible < key-up; and the ordinary v12 control stays uncancelled and reports `release`. Missing custody or event evidence is STOP/FAIL.
- **C:** The owner may define cause at the sampled decision point rather than at the later key-up side effect. This forced interleaving establishes possibility, not frequency under normal scheduling.
- **U:** Host-local macOS/Python 3.14.5, one forced schedule per case, fake Xlib only. No X server, physical input, GUI, application, game, model, task effect, recovery, or formal/live allocation. This does not establish end-to-end v39 cancellation publication or a user-visible consequence.

## Reproduction

From this directory, `python3 -B candidate.py` is the single frozen candidate invocation; it exited 0 and its raw output is retained. `python3 -B audit.py` independently checked the saved raw and exited 0. The audit's PASS label denotes successful counterexample reproduction. `candidate.started.json`, `FREEZE.json`, `RUN.json`, `ENVIRONMENT.json`, `AUDIT.json`, stdout, exit codes, and `SHA256SUMS.txt` bind the executed source and result.

The experiment used no container because all Xlib calls were replaced by an in-memory fake and the question was the ordering of two Python threads around a Boolean sample; it opened no host display or external service. No consumed C01/C02 allocation or retained raw was rerun or modified.
