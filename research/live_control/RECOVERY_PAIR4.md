# Registered recovery comparison — pair 4 A audited, B pending

Seven of eight registered episodes have executed. OpenTTD pair 4 uses depth 3,
pair label 204, A then B. The canonical save fixes the starting world; the label
is not an RNG override. `recovery_pair4_v1.py` combines the unchanged depth-3
setup/recovery logic from pair 2 with the road steps and finish timeouts from pair 3.
The runner source hash is captured in A's execution metadata and must be retained
for B. B has not run.

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
No task input was retried. Do not restart A. Next run B once with the unchanged runner.
No paired effect, token saving, human-speed claim, or model qualification yet.

Reproduce the audit in the Linux research environment:
`python3 research/live_control/audit_recovery_pair4_a_v1.py`.
