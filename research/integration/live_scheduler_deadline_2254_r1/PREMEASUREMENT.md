# #2254 live two-surface scheduler timing rung — premeasurement

This is a smallest model-free empirical rung under open Issue #2254. It does not close the Issue and does not claim model/task value.

## H
With the same native-derived two-surface record stream, unrelated noncritical backlog can make GLOBAL_FIFO miss a 100 ms critical-delivery deadline; CRITICAL_HEAD_FIRST can avoid that miss but starve unrelated noncritical state under a sustained critical head stream; DEADLINE_FAIR with burst limit 3 can preserve per-session FIFO, type already-expired critical evidence, and bound the selected noncritical wait to 50 ms in the frozen schedules.

## T
Provided Linux x86_64 container, CPython 3.13.5, private Xvfb and Python-Xlib. Three fresh X11 client surfaces A/B/C; A/B are watched, C is an unwatched focus sink. A separate watcher process receives real core-X11 FocusIn/FocusOut and captures real 32x32 XGetImage STATE bytes. Six schedules x three fresh server lifetimes = 18 formal cases: idle_state, backlog_deadline, critical_pair, fairness_starvation, expired_critical, cross_session. After each live schedule is captured, all three scheduler policies are released concurrently against the exact same immutable records. Fixed synthetic planner-service cost 8 ms/item; critical age budget 100 ms; fairness critical burst 3; selected noncritical wait bound 50 ms. Delivery age starts at watcher observation, not physical focus transition.

## D
PASS_LIVE_SCHEDULER_BOUNDARY_SCOPED only if all 18 cases/source/process identities reconcile and the independent raw-only audit passes: backlog_deadline makes GLOBAL_FIFO exceed 100 ms while both priority policies deliver the A FOCUS_LOST record within 100 ms; fairness_starvation makes pure CRITICAL_HEAD_FIRST hold B STATE at least 70 ms while DEADLINE_FAIR delivers it within 50 ms; critical_pair preserves A loss/gain order; expired_critical is typed EXPIRED by DEADLINE_FAIR; cross-session identity never mixes; idle produces no critical event; all policy outputs have authority=false. Missing evidence/process/source is STOP/HOLD; complete gate mismatch is FAIL. Comparator misses remain comparator failures, not candidate PASS by themselves.

## C
The 8 ms service time and schedules are explicit directed load, not a natural model-latency distribution. Criticality comes from the typed focus-event fixture. Threads share one CPython process for policy execution; the watcher and surfaces are separate processes. X11 watcher reception is not physical event time. This does not test real model interruption or application effects.

## U
No model/provider, tokens, task recovery, keyboard/mouse input, production runtime, human-tempo, natural failure rate or product claim. #2254 remains open even on component PASS. A later model-facing allocation must separately freeze model/task/effect gates.

Formal allocation ID: `live-scheduler-2254-r1-20260922-01`.
Construction uses `--construction` and is excluded. Formal output refuses overwrite; one invocation only, no replacement/tuning after first result.

## Construction status before freeze
Construction attempts 01–05 are retained in `CONSTRUCTION_INCIDENTS.md`; no formal case was consumed. Construction-06 completed the four excluded live families with all actor/watcher/Xvfb exits zero, integrity audit errors empty, and ten copied-evidence mutations rejected. Its fairness diagnostic was CRITICAL_HEAD_FIRST 84.808192 ms versus DEADLINE_FAIR 27.918909 ms for the selected B state; these construction values are excluded from formal inference and did not change the frozen 70/50 ms gates.
