# Ordinary fixture target-layer diagnosis — 2026-10-08 JST

**SUPPORT_FIXTURE_TARGET_LAYER:** two first ordinary regression cases, 48 saved-data checks passed. This repairs the diagnosis of the six-case fixture failure; it does not turn the original application-prefix result into PASS. No held key, pacing, full CLI, model or original allocation replay was used.

| Target given to unchanged native backend | Same wait | X focus before q | Tk focus before q | App result |
|---|---:|---:|---|---|
| Entry internal XID | 100 ms | 4194318 | None | empty; no events |
| Top-level wrapper XID | 100 ms | 4194317 | .!entry | q; KeyPress/KeyRelease |

Both runs used the byte-identical original recipient with `focus_set()` (no force), exact #8308 backend/core/sequence `dae92e12097907e860f68d6ee22a10cb23ace442`, a fresh authenticated TCP-disabled Xvfb and autorepeat disabled. Both native journals recorded q press/release, both execution receipts completed, both final readbacks were neutral, and both app/Xvfb pairs exited0 without forced kill. Entry/root/wrapper XIDs were resolved and recorded independently through the X server. The only policy difference between the two new cases was the target layer; each had the same100 ms post-focus delay. This is one observation per case, not a latency or reliability study.

The two cases, literal expected outcomes, bounds, decision rule and limits were recorded in the archived protocol and source-freeze before input; parent #57 claim6040999374. The ordinary fixture question was whether selecting the actual top-level wrapper allows Tk to route to its remembered Entry while an internal native focus does not. The saved observations support this in the owned Debian arm64 guest. A100 ms delay by itself did not repair the internal-target case. Other applications, window managers, callbacks and target types remain untested; do not generalize wrapper promotion to arbitrary runtime targets.

This reuses established Tk behavior, not a new input mechanism. [Tk focus documentation](https://www.tcl-lang.org/man/tcl8.6/TkCmd/focus.htm) describes remembering a child until top-level focus arrives and maintaining X focus at the top-level while managing child focus internally. Existing main also retains direct-X-focus construction failures and wrapper-target repair in `research/integration/public_api_effect_gated_recovery_v1/REPORT.md` (construct01/03/04/05); `caps_text_boundary_k8n4_v1/study/app.py` explicitly establishes Tk focus. Those records motivated this small repair check; their outcomes were not counted as new data.

Adopt for this synthetic fixture: bind the backend to the resolved top-level wrapper, retain the Entry as the application recipient identity, and require recipient-level readiness/effect observations. Backend focus success remains insufficient as a general application-ready claim. The regression runner is a scoped fixture repair, not a production runtime patch. The original six cells and their frozen failing auditor remain immutable.

Measured resource gate: CPU1, RAM512MiB, swap0, tasks128, UID501, source not writable, only loopback active/no IPv4 routes. The owned VM was restarted solely for this diagnosis, then stopped after export; transient unit inactive/dead and no experiment children left. No foreign resource or shared Docker modification. Original Docker preparation failure and nested mount-isolation limits still apply.

Run `python3 verify_saved.py` in this directory for read-only archive/source/recipient comparison, reproduction of the48-check audit, and four corruption controls (wrong native focus, missing app text, nonneutral final keys, bad driver exit). No native runner, Tk or Xlib is executed by verification.
