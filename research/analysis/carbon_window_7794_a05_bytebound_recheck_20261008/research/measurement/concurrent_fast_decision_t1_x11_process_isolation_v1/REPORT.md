# #1421 first construction outcome

Decision: **STOP_PROCESS_ISOLATION_INSUFFICIENT**. Scientific disposition: **NONE**.

The source-frozen construction allocation ran exactly once: one ACTIVATE18 matched pair / two fresh Python child processes. Formal remained 0; reruns/replacements/tuning remained 0.

Observed:
- child exit codes: 2 / 2;
- both children independently closed controller/scorer Xlib connections, destroyed Tk and terminated Xvfb;
- post-supervisor residual Xvfb sockets/processes attributable to the allocation: 0;
- the predecessor #1384 multi-session XIO/Xserver-teardown signature did **not** recur;
- both children stopped with `TypeError: string argument without an encoding` while the scorer path converted Xlib image data with `bytes(img.data)`;
- baseline produced no sends; candidate sampled WATCH at all eight 5 ms boundaries, produced no sends and had no retained state transitions;
- no complete scorer/terminal-key result exists, so task-effect science is not evaluable.

Raw result SHA-256: `e05e3f141f74870518c515907d4ec6543cad61735cd5376e41aa9c4661844d4c`.
Audit SHA-256: `4f6c495031fea164aef0c45f8baeab6f6836632738dbf45c1265c0551d48d19c`.

Interpretation is limited: process isolation removes the exact predecessor teardown failure but is not sufficient for an eligible construction. A distinct successor must retain this first outcome and change one harness factor at a time; no #1421 rerun or formal execution is allowed.
