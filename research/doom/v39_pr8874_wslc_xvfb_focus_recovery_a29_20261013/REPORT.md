# V39 focus-target release observation A29 — result

Decision: **FAIL under the preregistered focus-state gate; remaining criteria pass in the retained virtual X11 run.** One WSLc candidate execution; no retry.

The Xvfb client saw KeyPress for keycode 25 on old window A (2097152), then KeyRelease for the same keycode on new window B (2097153) after A observed FocusOut. The server keymap was down while held and up after release. The backend emitted one admission-linked explicit-UP receipt with owner-thread XTest KeyRelease/XSync verification. `release_all()` verified empty keys/buttons/unknown keys, the admission cache was empty, the owner stopped, Xvfb exited 0, the analyzer accepted one hold, and the WSLc container was removed. The observed focus-out-to-owner-sync interval was 0.292 ms.

The candidate did not query and retain the current input-focus window after switching focus. Since the preregistration explicitly required that independent state observation, the result remains FAIL despite the KeyRelease arriving at B. The independent auditor confirms this missing gate and the positive release evidence. No claims are made about Doom/MAP01, physical input, model latency, or task effect.

Raw result: `results/a29-01/raw.json`; independent audit: `results/a29-01/audit.json`; frozen source identity: `SOURCE_MANIFEST.json`; original protocol: `PREREGISTRATION.md`. WSLc warned that host cgroup/swap enforcement is unavailable; no hard memory cap is claimed.

