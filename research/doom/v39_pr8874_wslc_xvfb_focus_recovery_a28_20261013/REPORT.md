# V39 focus-loss recovery A28 — result

Decision: **FAIL under the preregistered measurement/cleanup gate; useful partial positive release evidence.** This was one offline WSLc run, no retry.

The candidate observed a matching KeyPress and FocusOut while `w` was down. The V39 backend then produced one owner-bound explicit-UP receipt linked to the exact admission. Its owner-thread KeyRelease/XSync completed, and the owner-side X11 keymap sample changed from down to up. The focus monitor also recorded `owner_release(reason=focus_changed)` with verified empty keys/buttons/unknown keys. These observations show that the virtual X server did not retain the key after this focus transition.

The preregistered observer did not receive a matching KeyRelease on the original window after it lost focus; it timed out. The candidate therefore did not reach its explicit `terminal_release()` call or record the admission-cache count after terminal release. Owner shutdown subsequently recorded a verified empty state, but that does not satisfy the preregistered terminal-path/cache gate. The experiment is a FAIL as frozen, not a PASS rewritten from component observations.

Independent audit: `results/a28-01/audit.json` (`PASS_METHOD_SCOPED_AUDIT` means the auditor verified the retained decision and evidence, not that the experiment passed). Raw bytes are retained at `results/a28-01/raw.json`. The WSLc command exited 0 because the candidate catches exceptions and serializes them; the raw candidate status is an event-observation timeout. Xvfb exited 0 and WSLc `--rm` removed the container. WSLc warned that host cgroup/swap enforcement is unsupported; no hard memory-limit claim.

Scope: Xvfb/XTEST, virtual X11 key state and current-workspace backend plus frozen V4/V12 owner. No physical desktop, game/MAP01, threat, model wait, navigation, survival, task effect, visual guard, or live/formal allocation. Exact frozen input identities are in `SOURCE_MANIFEST.json`; preregistration is unchanged.
