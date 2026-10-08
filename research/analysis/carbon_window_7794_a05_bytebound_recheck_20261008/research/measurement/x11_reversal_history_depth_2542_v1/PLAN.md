# Issue #2542 — five-sample X11 reversal history-depth successor

Allocation: `x11-history-depth-2542-20260922-01`.
Owned additive path: `research/measurement/x11_reversal_history_depth_2542_v1/`.
Owned branch: `research/x11-history-depth-2542-20260922-v1`.

## H
Hold the #1335 saturated-red X11 centroid path, logical 100 ms sample geometry, 7.3 px full-step motion, +/-1.0 px point envelope, +/-2.0 px displacement compatibility band, one-reversal motion family, ages {25,50,75,100,150,200} ms, both post directions, phases 0..99, and fail-closed direction semantics fixed. Change only retained history from newest three samples (H3) to newest five (H5). H5 should reduce UNKNOWN while emitting no wrong direction. H3 must reproduce the retained #1335 counts; H5 must reach >=0.95 accuracy at each 100/150/200 ms age.

## T
Provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6, Python-Xlib 0.15, private Xvfb 320x200x24 with TCP disabled and ephemeral Xauthority. No model/provider, external network experiment, host desktop, keyboard/mouse input, user data, or shared runtime mutation.

Formal corpus: 6 ages x2 directions x100 phase identities =1200 trajectories. Each trajectory renders/captures five sequential logical samples at -phase, -100-phase, -200-phase, -300-phase, -400-phase ms, oldest to newest. One captured five-frame trace feeds both H3 (newest three) and H5 (all five), so localization evidence is matched. Four private Xvfb/Tk sessions own phase blocks 0-24,25-49,50-74,75-99. Total 6000 real XGetImage scanlines. Raw scanline bytes are retained losslessly as zlib+base64 per frame.

Decision rule: each 100 ms interval is full-sign compatible iff observed displacement lies within 2.0 px of +/-7.3 px. For a candidate current direction s, a feasible at-most-one-reversal world must have all intervals before a possible reversal compatible with -s, all after compatible with s, with at most the single interval containing the reversal unconstrained. Reversal before oldest and after newest are explicit cases. Return a direction only when exactly one current direction is feasible; otherwise UNKNOWN. The newest-three version must equal the #1311/#1335 three-sample rule on every formal row.

Construction uses only ages {40,110,175} ms and half-ms phases {0.5,33.5,66.5,99.5}; it is excluded. Freeze source, gates, environment and construction evidence before formal. Exactly one formal invocation, no same-ID rerun/replacement/tuning.

Controls after formal are read-only/copy-based: missing history, duplicate/nonmonotonic timestamps, stale newest sample, cadence mismatch, wrong depth, altered centroid/scanline, altered decision count, source hash, and row-count mutations. A >1.0 px authored/observed mismatch must be rejected by the auditor and cannot be treated as a valid science row.

## D
`PASS_X11_HISTORY_DEPTH_RECOVERY_SCOPED` only if all 1200 trajectories/6000 frames, 4 sessions and source/process/cleanup records reconcile; H3 formal age counts exactly reproduce #1335 candidate accuracies {25:.15,50:.40,75:.65,100:.90,150:1.00,200:.89}; H3 generalized rule equals the frozen legacy rule on every row; H5 and the independent auditor agree on every row; wrong-direction count is zero for both arms; H5 accuracy >=.95 at 100/150/200 ms; every H5 non-UNKNOWN has exactly one feasible current direction; every captured point error <=1.0 px; malformed/stale/order/cadence controls fail closed; copied-evidence corruption controls reject at least 10 mutations; formal invocation1/reruns0.

If safe but H5 misses a recovery gate or does not improve enough to establish unique direction, retain `HOLD_HISTORY_DEPTH_INSUFFICIENT`. Any wrong direction is `FAIL_HISTORY_DEPTH_SAFETY`. Point-envelope, source, process, audit or denominator contradictions are `STOP/FAIL_INTEGRITY` as applicable. A PASS is geometry-equivalent history-depth evidence only and does not establish wall-clock cadence, semantic target discovery, task effect, model benefit or production control.

## C
More history can only help under the frozen known-speed/at-most-one-reversal family and valid point envelope. It cannot repair acceleration, multiple reversals, stale lineage or a wrong localization bound. Correlated Tk rasterization is permitted by the hard bound and may differ from independent noise. H3 reproduction is an explicit transfer control, not a relaxed gate.

## U
No real 10 Hz waiting/scheduler behavior, arbitrary visuals, compositor/Wayland, physical input, model-facing decision, token/latency benefit, human-tempo or production claim. Same-author separate auditor is not independent human review.
