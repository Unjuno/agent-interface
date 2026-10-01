# Registered recovery comparison — both pair 4 arms audited

All eight registered episodes have executed. OpenTTD pair 4 uses depth 3,
pair label 204, A then B. The canonical save fixes the starting world; the label
is not an RNG override. `recovery_pair4_v1.py` combines the unchanged depth-3
setup/recovery logic from pair 2 with the road steps and finish timeouts from pair 3.
The runner source hash is captured in A's execution metadata and must be retained
for B. B completed with that unchanged runner.

| Measurement | A | B |
| --- | ---: | ---: |
| Recovery reads / reported orchestration calls | 4 / 4 | 4 / 1 |
| Total socket exchanges | 16 | 16 |
| Exact frames / unique events | 7 / 53 | 7 / 53 |
| Capture to final terminal | 103.698888 s | 50.881575 s |
| Capture to independent evaluation | 112.397007 s | 65.582765 s |

B's full recovery history and original image were visible together before task
input. Open/build views and original images were also visible; no extra input or
image retry occurred. Its independent guard score and cleanup passed. The B audit
verifies all raw slices, source hashes, four pending-clock reads (three historical,
then own), task-source history, exact frames, score and cleanup. The difference
is three fewer recovery orchestration calls, with no socket-read reduction.
Timing is descriptive: A's image anomaly, extra inspection and review/commentary
remain included. Do not attribute the full elapsed difference to the helper.

A required four separate model orchestration calls with one read each. The first
three returned the three queued historical clocks; the fourth returned the own
clock. No physical input was sent during recovery. Own-clock history was reviewed
before opening the road toolbar. Open/build completed, independent guarded scoring
passed, and the bridge exited 0. Cleanup reports all owned processes exited and
the canonical save unchanged. The source/frame/event audit passed: seven exact
frames, 53 raw events fully covered by 16 socket exchanges. The four recovery
slices and every intermediate assembled history match the raw event positions.
The first three clock identities match the queued historical requests; the fourth
matches the outstanding own request. The task source is that final history.

Initial capture to final terminal was 103.698888 seconds, and to independent
evaluation 112.397007 seconds, including model review, commentary and the additional
image-only inspection. These are elapsed observations, not a qualified performance
comparison. Exact model configuration and actual token/cost accounting are missing.

Presentation anomaly: the same sequence-2 PNG appeared correctly at recover1 and
recover3, but black at recover2, recover4, and one additional image-only inspection.
The selected path and SHA remained the same. The decision used the previously
visible identical sequence-2 image plus the reviewed final history; the subsequent
open/build original images were visible. Preserve this limitation and extra
inspection; do not call this a clean final-history-plus-image delivery.

Evidence is archived in `results/recovery-pair4-01/A`;
`presentation.json` records these observations. The sequence-2 PNG has nonzero
RGB content (each channel spans 0–255) and matches the decoded AIT frame. Its SHA
matches every recovery selection. This rules out an all-black saved source; it
does not locate the failure within image-tool processing or model presentation.
No task input was retried. Do not restart either arm. Next aggregate all four pairs
with the registered median/range and per-domain/depth results; keep all failures.
No token saving, human-speed claim, or model qualification yet.

Reproduce the audit in the Linux research environment:
`python3 research/live_control/audit_recovery_pair4_a_v1.py`.
The corresponding B audit is `python3 research/live_control/audit_recovery_pair4_b_v1.py`.
