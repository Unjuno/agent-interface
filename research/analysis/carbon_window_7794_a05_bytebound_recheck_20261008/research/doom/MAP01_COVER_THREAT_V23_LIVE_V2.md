# V23/schema-v3 live threat exposure

The separately frozen `map01-cover-threat-v23-live-02` allocation completed its
first and only run. Astra-low made 12 decisions while normal MAP01 continued at
35 tics/second. The run ended alive and unfinished after 143.345 seconds with
two kills, 28% health, no death and no map exit. This is mechanism evidence,
not a successful hero run.

The repaired contract finally received the required live exposure. Decision 3
saw enemies and ammunition, then authored
`strafe_right/fire/strafe_left`. Decision 4 executed that exact policy during
inference and authored the same policy again. Decision 5 executed the second
policy. All 16 cover programs compiled to exactly ten seconds, ended on coast,
were accepted, and verified input release. Four renewals had a maximum
release-to-readmit gap of 21.259 ms.

The exposure also isolates the stale-policy problem. The exact decision HUD
frames show health `100,100,100,100,97,74,28,28,28,28,28,28`. Decision 4
reauthored the attack/evasion policy at 97% health. The next decision began at
74% health with different geometry and an assessment that the raised ledge
blocked the route. Nevertheless, the already-authored policy repeated during
decision 5 inference. A posthoc replay of every lossless health-region sample
detects the first change 1.623 seconds after cover admission, 9.802 seconds
before that model call returned. The following decision frame was 28% health.

This does not prove that the cover caused the damage or that cancelling it would
improve survival. Each decision interval contains other gameplay, pixel change
does not reveal whether health rose or fell, and this is one run. It does prove
that the runtime had fresh visual evidence that a declared policy dependency
changed long before the planner boundary, yet v23 could neither invalidate the
running cover nor refuse the concurrently computed stale primary action.

The retained package includes all raw model-call records, runtime event logs,
exact decision frames, and a lossless health ROI for every cover observation.
It omits the 97.8 MB complete PNG/AIT stream and states that selection in its
manifest. Run the audit with:

```sh
PYTHONPATH=research/live_control python research/doom/audit_map01_cover_threat_v23_live_v2.py
```

The smallest next mechanism is stop-only. In a newly versioned controller, an
opt-in region guard may cancel an existing cover and discard the model action
computed from the invalidated source. `UNCHANGED` leaves prior authority alone;
`INVALIDATED` and `UNKNOWN` require a fresh decision. The guard must not infer
damage direction, authorize an evasive fallback, or treat region change as task
success. A new preregistered allocation is required for any live test.
