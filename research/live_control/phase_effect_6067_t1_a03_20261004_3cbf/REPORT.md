# A03 formal result: STOP_RENDERED_EXPOSURE_GATE

Formal freeze7708112d2c1d07b23941abf643abb804a1be27c5,
SHA256 d997e605e2f53db6922eda5f631185bd45d32076398e3b59d79d5add4601db14.
One native formal producer ran2026-10-03T16:32:02.155311852Z–16:32:14.228488305Z,
terminal2/OOMfalse/restart0. **8/114cells started,7qualified,64actual captures
retained;5/108pulse cells started. Official scientific auditor0, retries0.**
No replacement, threshold widening, readiness pooling, or incomplete-family
phase-effect estimate. Parent#6067 and full ROADMAP remain open.

First failed cell c007: rotated[0,3,6,9], source phase1, width10ms. Source cue3
stable exposure **4.971449ms**, below frozen5ms minimum by **0.028551ms**.
All24children across started cells terminal0, neutral keys/final clear. Source50
pins/FREEZE and guest pre/post bytes unchanged, raw copied0, delivered copy
identical to external execution output. Actual CPU1/512MiB/swap0/PIDs64.

| Cue3 exposure decomposition | ms |
| --- | ---: |
| Draw-wait return lateness | 0.584423 |
| Wait return → native paint start | 4.233736 |
| Native draw/XSync interval | 0.525046 |
| Clear-start lateness (subtract) | 0.314654 |
| Exact nominal exposure shortfall | 5.028551 |

The post-wait snapshot spans4.187195ms; return→snapshot begin0.024708ms and
snapshot end→paint0.021833ms complete the4.233736ms bracket. CPU-stat read
within that snapshot spans0.682922ms. This localizes recorded wall time to an
instrumentation-containing interval; it does NOT distinguish instrumentation
CPU cost, syscall delay, descheduling, physical-host load or causal rootcause.
Wait lateness alone is smaller than the observed shortfall; no consumed B01
diagnostic outcome is rewritten/promoted by this posthoc decomposition.

Read-only failure retention checks cover144waits/288snapshots, typed streams,
per-process continuity and disjoint shared CPU reads. All individual measured
wait pre/post leaf-throttle deltas0, including the failed draw/clear pair.
However whole formal leaf counters grow1→8 and throttled_usec25771→96054 across
saved reads. **Do not claim no quota events, no host contention or no scheduling
effect.** All failed-cell capture starts remain within10ms (max2.387416ms).

The prior EXCLUDED readiness separately passed5cells/40captures and one saved
readiness audit with15controls, independently reviewed. It did not qualify all
phase/arm cells: this actual formal STOP demonstrates that distinction. Prior
host prelaunch STOP, original ineligible freeze/source tar, A01/A02/B01/C01
history remain unchanged. Frozen prospective README/STATUS are timestamped
snapshots; READINESS_REPORT/READINESS_REVIEW and this report are later outcomes.

Independent first-failure review pending at report creation. Preserve complete
raw, source/wait/pixel journals, Docker inspection, original first reason,
transport/source bytes, and explicit formal auditor0. Any successor must be a
genuinely new question/prospective allocation; do not replay this consumed114
block or silently move telemetry/change exposure gates to salvage a PASS.
