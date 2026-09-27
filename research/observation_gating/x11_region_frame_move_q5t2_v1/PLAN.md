# X11 window-relative region across window moves — Issue #4439

Allocation: `x11-region-frame-move-4439-localdocker-v1-20260927`  
Main snapshot: `c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd`  
Owned branch: `research/x11-region-frame-move-4439-20260927`  
Additive path: `research/observation_gating/x11_region_frame_move_q5t2_v1/`

This is a pre-execution freeze. The Issue #4439 hypothesis, policies, 27-case schedule, gates and limits are preserved. This local Docker allocation amends only the fixture/environment detail below; it does not change a prior result or touch predecessor files.

## H — hypothesis

For the same live X11 window XID and immutable target-relative pixels, a pinned initial screen rectangle is stale after a move; a refreshed root translation works if the move precedes resolution but fails if the window moves between resolution and capture; direct `WINDOW_CLIENT` capture remains bound to the same window content in all three schedules. Mismatch is a stale-coordinate observation, not target absence or action authority.

## T — frozen allocation

- Three policies (`PINNED_SCREEN`, `REFRESH_SCREEN`, `WINDOW_CLIENT`) × three schedules (`STABLE`, `MOVE_BEFORE`, `MOVE_BETWEEN`) × three repetitions = **27 first-outcome sessions**. Each session has a fresh private authenticated TCP-disabled Xvfb and one override-redirect 120×80 Xlib window at (20,20), moved to (220,160) when scheduled. The window has a fixed non-flat row-pattern; candidate policies receive no semantic labels. Scoring-only oracle captures the same window XID after candidate capture.
- The original Issue proposed a Tk fixture in a supplied Python 3.13.5 environment. This PC's matching cached offline image has Python-Xlib 0.15/Xvfb but not Tk shared libraries. Frozen local fixture therefore creates/maps/moves the same X11 window directly via Xlib; no Tk behavior is claimed. Python is 3.11.16, Debian 13.7, Python-Xlib 0.15, Xvfb 21.1.16, Xauth 1.1.2, libX11 1.8.12. Docker Desktop image: `agent-interface-string8-4638:candidate-v1`, ID `sha256:1c334ebd65f4b1bfe81cc84c90780ea01e6f70c0f7b18cd89c09e03406460238`, linux/amd64. Pull never; network none; read-only source/root; `/tmp` is private bounded tmpfs; one CPU, 512 MiB, 64 PIDs. RTX 3080 is deliberately unused because the X11 coordinate/capture mechanism is CPU-bound and has no GPU treatment.
- Each row retains both candidate and scoring-oracle XGetImage bytes losslessly as deterministic gzip+base64, uncompressed/compressed SHA-256 and lengths; also coordinates, image hashes, capture monotonic bracket, Xvfb PID/expected SIGTERM exit `-15`, and Xauthority mode. Runner flushes/fsyncs each row. Source is `runner.py`; raw-only independent auditor is `audit.py`. The auditor imports no runner code, decompresses/re-hashes pixels, regenerates the exact case denominator/coordinate schedule, validates pattern immutability and expected match matrix, checks every process/authority receipt, and applies 13 separately copied corruptions.
- Exact source SHA-256: runner `1c53f09b603158cff32321906af39bbbcf19d232846a92216c03574a700780f3`; auditor `df75f04d7686e78367ac202a7c4a14b625b651efc9a4c5cbecc95efb4c097526`.

## D — frozen decisions

`PASS_X11_REGION_FRAME_MOVE_BOUNDARY_SCOPED` requires 27/27 unique sessions; correct frozen geometry and candidate coordinate receipts; immutable target pattern; STABLE all 9 matches; MOVE_BEFORE `PINNED_SCREEN` 0/3 and other policies 3/3; MOVE_BETWEEN `WINDOW_CLIENT` 3/3 and root-coordinate policies 0/3; all pixel bytes/hashes/lengths reconcile; all owned Xvfb processes terminate with the recorded controlled `-15`, private auth files are mode 0600; independent audit errors are empty and all 13 corruption controls reject. Any complete contrary coordinate result is `FAIL_COORDINATE_FRAME_PREDICTION`; any source, image, process, coverage, pixel, or audit discrepancy is `HOLD/STOP`. No retry, replacement, post-result tuning or pooling.

Construction uses the same frozen code but a disjoint 9-case one-repetition subset; it is excluded from the 27 formal rows. Only after source/gate GitHub readback and construction audit pass will the single formal invocation occur.

## C — alternatives/confounds

No window manager or compositor is present; the window is cooperative, mapped, opaque and retains fixed pixels. Moves are serialized XConfigureWindow requests with XSync. X11 server event ordering and direct window-relative capture are the treatment. Root capture may see the exposed background after the window moves. This does not test asynchronous races, natural miss rates, app semantic identity, occlusion, destroy/recreate, resize, Wayland/compositors, or pixel freshness at later model consumption.

## U — limits

One synthetic X11 window/Xvfb image and one local Docker image/host. Does not establish Tk behavior, all applications, backend correctness, semantic target identity, action safety/authority, task correctness, latency savings, model utility, or production readiness. The narrower measured claim is only the X11 coordinate-frame/window-XID boundary described above.
