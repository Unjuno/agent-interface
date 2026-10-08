# TEMPORAL-SPECULATION-X11-PLANNER-GAP-R1-20260918-001

One integration factor: add a fixed planner-unavailable interval to the #1175 no-authority branch mechanism.

Private scripted X11 fixture only. Matched current pixels at x=160. Histories right/left; future magnitude1/magnitude2 balanced. K=2 fixed. CURRENT=(-1,+1), TEMPORAL right=(+1,+2), left=(-1,-2), WAIT=none. Future realizes +100 ms after current alias; planner returns +130 ms. A local branch can trigger fixture EFFECT only after fresh future capture exactly matches the branch, branch unexpired, current digest unchanged and external admission token true. Misses wait for planner return. No OS input/model/provider/shared runtime.

Formal: 12 matched scenarios x3 arms=36 fresh Xvfb/Tk sessions, counterbalanced order, displays 920..955. One supervisor invocation, reruns/replacements/tuning0. Expected local hits: WAIT0, CURRENT6, TEMPORAL12. Frozen gates: temporal future->effect median<5 ms,p95<8; CURRENT−TEMPORAL mean>=10 ms; WAIT−TEMPORAL mean>=20 ms; wrong/stale/authority effects0; exact matched current digest; cleanup/exceptions0.
