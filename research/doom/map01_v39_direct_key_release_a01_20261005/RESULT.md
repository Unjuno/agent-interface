# Result: MAP01-V39-SELECTED-KEY-OWNER-A01-20261005

Disposition: `PASS_SELECTED_KEY_PATH_CONTRACT` for the frozen in-memory fake-Xlib contract.

The one-shot candidate retained a clean control and an aggregate keymap-query failure case. Both cases emitted F8-down, space-down, space-up, F8-up, with no per-key keymap query between the two ups. The clean `release_all()` returned a verified-empty `owner_release`. In the fault case, the first aggregate keymap query raised `RuntimeError`, so that call produced no verified release record. The separate owner-close cleanup then sampled verified-empty state and stopped the owner. Raw and audit records are in `results/candidate-a01/raw.json` and `results/candidate-a01/audit.json`.

The candidate used the actual `session_v5.Backend.raw()` and `release_all()` method implementations and the exact frozen `input_owner_v10.py`. It supplied a minimal stub for the unrelated `session_v4` base class and in-memory fake Xlib/XTest objects. Thus the result checks the selected method/owner interaction and recorded control flow; it does not execute the complete backend inheritance chain, full V39 session/controller, or a real X server.

No real X server, OS input, ViZDoom, model, GUI, or container was started. This evidence does not establish physical key state, server delivery, task effect, useful feedback, threat response, bounded MAP01 recovery, or latency qualification. Treat it as a local component-contract result only.

Candidate and auditor were each invoked once. The auditor checked the frozen source and package hashes and validated the retained raw trace; neither one-shot program was rerun while preparing this note.
