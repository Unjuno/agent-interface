# Formal 06 — X input-focus identity in the X11 continuation route

**Disposition: `PASS_LIVE_INTERMEDIATE_FEEDBACK_AND_EXACT_EFFECT`** for this one synthetic fixture task. The parent Issue #3311 remains open and unaccepted.

## H / T / D / C / U

- **H:** In the pinned WM-less Xvfb fixture, `xdotool getwindowfocus` can identify the Chromium input-focus XID even when `_NET_ACTIVE_WINDOW` (`getactivewindow`) is empty. A fresh identity gate using that focused XID, live title, and exact target reference can safely admit the Save and Confirm clicks. Mismatch must still refuse before input.
- **T:** Consumed allocation `ISSUE3311-LOCAL-X11-INTERMEDIATE-FEEDBACK-20260928-06`, from frozen branch commit `25af888982051e673b69e9fce3253d676aac214f`; base commit recorded in `FREEZE_FORMAL06.json`. The no-GUI Docker preflight ran once, then the frozen formal runner ran once in local OrbStack on image `sha256:dff1c7b56201b4c299883655d98aee3b3f8d7c0c6dd1e4ad6320b942fb5d17fb` (`linux/arm64`, CPython 3.11). Formal container: network-none, read-only root and source, isolated Xvfb `:97`, 1 CPU / 2 GiB / 512 PIDs / 128 MiB shm; only `/out` was writable. No other container was live at formal launch. Model calls, retries, and replacements: 0.
- **D:** Three hash-bound screenshots show `EDITING` → `CONFIRMING` → `SAVED`. In both fresh admissions, `getactivewindow` returned empty while `getwindowfocus` returned the observed Chromium XID `2097155`; title and exact `window:2097155/#save` or `/#confirm` target matched. Both clicks completed, each button release was verified with an empty held-input set, both state effects were confirmed by the local fixture server, and exactly one submission carried `AI-3311-UNIT-01`. Runtime receipt: `TASK_SUCCEEDED`, 2 transitions, 0 frontier-model resumptions. The independent raw-only auditor passed 30/30 checks with `errors=[]` and pinned result SHA `7c4773395c6657a50ec36b299ca6e059370e9f3dc88d904ce7a94ab079d4dfab`.
- **C:** One deterministic synthetic Chromium/Xvfb task and one local server oracle; predecessor formal05 remains unchanged. This tests the *input-focus XID route* where the active-window query is empty; it is not a matched policy/economics comparison. The runtime receipt's ~1.058 s is descriptive for this single run only and is not a latency or speed claim.
- **U:** No model/provider call, cold/warm/invalidation/repair comparison, six-task workload, meaningful-benefit test, broad GUI reliability, human-tempo result, task transfer, or product claim. Formal06 is a mechanics rung only and does not satisfy #3311's full acceptance criteria.

## Reproduction and retained evidence

The exact frozen commands, image/source identities, resource limits, and one-shot counts are in `FREEZE_FORMAL06.json` and `CONTAINER_RUN.json`. Raw result, event journal, and three PNG observations are retained beside this report. The independent auditor was run as a separate host process after the container exited; its exact output is `AUDIT.json`. Preflight output is `PREFLIGHT_RESULT.json`. `SHA256SUMS` binds these files and source inputs.

No runner or allocation retry is authorized. Preserve this result unchanged; the next scientific step must be a separately frozen test that addresses the actual #3311 cold/warm/invalidation/repair comparison and all-attempt accounting.
