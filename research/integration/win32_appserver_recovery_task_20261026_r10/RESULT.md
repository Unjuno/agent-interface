# R10 result — runtime prerequisite failure retained

**Classification: `FAIL_RUNTIME_PREREQUISITE_RETAINED`.** R10 ran on the user-authorized Windows PC using Python 3.11.9. The bounded AppServer pipe client refused to start because Windows requires Python 3.12 or later. The runner stopped before a model turn and before any task input.

The phase-one recovery gate passed: SHIFT-down was independently observed while the producer callable was held before native `SendInput`; one public cancel led to retained `recovered / release_confirmed=true`; same-generation native readback found SHIFT up; recovery took 16 ms against the 3 s limit. A fresh PID/generation was started, and the old-generation probe returned `TARGET_GENERATION_CHANGED` with `input_dispatched=false`. The old fixture exited 0, foreground restoration passed, no task effect occurred, and no WSLc or Docker operation was used.

The frozen [`audit.json`](audit.json) has a path-resolution defect: it resolves packet-relative pretrial hashes from the repository root. The additive [audit follow-up](audit_followup.json) verifies all 5 pretrial and 27 raw hashes and confirms the retained runtime failure without modifying the original outcome. R11 uses Python 3.13.14 and is the distinct continuation attempt.

The held operation is injected before native `SendInput`; no OS/kernel hang or arbitrary-I/O guarantee is established. R10 has no model, task effect, efficiency or reliability result.
