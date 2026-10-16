# Construction history — allocation TEMPORAL-CONTRACT-X11-PROPERTYNOTIFY-R1-20260922-002

These are construction/harness outcomes, not scientific formal results. No row from a stopped construction is pooled into the formal allocation.

- Construction 01: **STOP_ENVIRONMENT_PROPAGATION**. Historical #1801 runner restored parent DISPLAY/XAUTHORITY before python-xlib Display creation; this supplied container had no parent ~/.Xauthority. Scientific rows saved: 0.
- Construction 02: **STOP_CASE_PROCESS_ISOLATION** after moving Xlib connection creation inside the private environment. Tk/Xlib process-level XIO occurred when the next fresh Xvfb reused display :0. A completed case was not serialized; no row is reconstructed. An owned orphaned Xvfb was terminated; no active socket remained.
- Construction 03: **STOP_CASE_PROCESS_ISOLATION** with explicit :90/:91 display numbers. Tk still retained process-level display lifetime across sequential fresh servers; XIO occurred and the owned :91 server was terminated. No row is reconstructed.
- Construction 04: changed only orchestration so every fresh Xvfb/Tk case runs in a fresh Python process. The event schedule, A3 monitor, atoms, delta, independent oracle and decision gates are unchanged. Result: **PASS_CONSTRUCTION_ELIGIBLE**, 3/3 worker exits 0; POSITIVE=SATISFIED, EXPIRE=EXPIRED, NO_RESTART=EXPIRED. Result SHA-256 `90188c73af89c5cbf1d0a2896a3f73e4d22062e6d8e4575aaed61dc21963f3ef`; audit SHA-256 `5f895d47debc753616678c42d3598ccc44cf381f4aa22421332069ab4cb6a7a6`; corruption controls 5/5 reject.

Formal source/gates are frozen in FORMAL_FREEZE.json before the first formal invocation.
