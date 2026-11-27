# V39 Executor V3 Concurrent X Event Watcher A02

## Scope

A04's independent X event check was polled only after planner return, so it could not measure whether the event arrived earlier. A02 uses a separate X connection that drains KeyRelease events continuously on its own thread while the planner wait is active. It exercises current-main V39 invalidation/cancel logic, the in-process current-main Executor V3 class, and InputOwner V4/V12 against an Xvfb-backed adapter.

## Pre-registration (H/T/D/C/U)

- **H:** Continuous independent event draining will capture the Xvfb KeyRelease before planner wait returns; A04's late timestamp was a delayed-observation artifact rather than delayed key release.
- **T:** One hard-health arm from the retained seq2/seq3 observations, synthetic health 97→80, deterministic planner fake, current-main V39 cancellation helper, Executor V3 worker, and InputOwner V4/V12. A dedicated watcher starts before submission and drains from a separate connection. One candidate invocation.
- **D:** PASS_METHOD_SCOPED requires frozen hashes; Executor acceptance before X KeyPress; key down at observation; hard invalidation and matched cancellation; cancelled terminal with verified explicit owner keyup; independent KeyRelease observed before planner return; stale planner answer ineligible; final admission rejected; executor/owner/watcher stopped; clean Xvfb shutdown. Any failed check is STOP.
- **C:** Health drop and planner answer are synthetic. Xvfb is a real X server but the backend and planner are focused adapters. The concurrent timestamp is when a dedicated Xlib connection read the event, not hardware time. The Executor class runs in-process, not the production controller subprocess.
- **U:** No live game/model/device, semantic perception, production subprocess failure, hard-crash recovery, or live MAP01 allocation. WSL2; no network namespace or hard CPU/memory cap.

## Result

**PASS_METHOD_SCOPED.** The candidate ran once, exited 0, reported no errors, and Xvfb exited cleanly. The independent raw-only audit at `AUDITOR/audit_raw_a02.py` passed all 11 checks, including frozen source/input/candidate hashes.

The X event watcher started at 18,623,805,567 ns, before Executor acceptance at 18,625,778,697 ns. It observed the X KeyPress at 18,626,496,204 ns and the independent KeyRelease at 18,633,281,253 ns. Planner wait returned at 18,633,693,664 ns, so the independently observed release preceded planner return by 412,411 ns. The retained raw also confirms health hard invalidation, matched cancellation, a cancelled Executor terminal with verified owner-thread XTest KeyRelease/XSync and keymap-up receipt, planner answer ineligibility, rejected final action admission, and stopped executor/owner threads.

This supports the A04 instrumentation diagnosis: polling only after planner return caused its late *observation timestamp*. It is not a repeated A04 run and does not prove hardware-level timing. One sample establishes ordering in this bounded fixture, not scheduling reliability under load. Current Executor V3 is in-process and uses an Xvfb adapter; semantic perception/task success, production subprocess failure, process-kill recovery, and live-game behavior remain untested.

The raw candidate's free-text scope field labels the Executor V3 path "production". That descriptor is inaccurate: the retained source and execution use the current-main in-process `Executor` class and a test backend. This report and the freeze metadata define the actual scope; the raw file is preserved unchanged.

Exact source/input hashes and environment are in `FREEZE.json`; raw result and hashes are in `results/A01/`.
