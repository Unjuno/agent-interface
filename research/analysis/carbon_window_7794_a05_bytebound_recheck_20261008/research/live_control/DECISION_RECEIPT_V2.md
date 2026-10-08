# Compact report binding v2

V2 adds recorded clock/submit binding to the v1 evidence index. It requires exactly
one clock and one submit exchange, distinct request IDs, own echoed commands,
matching submitted/echoed command content, contiguous reply prefixes, matching
clock/source/submit sequence, a positive reported deadline, unique own admission
and final terminal, consistent step counts, and exact agreement with top-level
terminal/last_reply/continuation_batch. Historical or interleaved command records
require further review. A binding failure returns no bound program and an explicit
attention reason. A bound needs-decision terminal remains an interruption.

Recursive inspection surfaces nonempty `error`/`exception` and explicit false
`success`/`verified`/`exact`/`focus_samples_match` fields with source paths. Unknown
event names and top-level routine-event fields retain v1 attention behavior.
Unknown nested schemas are not fully validated. Malformed structures may raise an
error rather than produce an index. This is a narrow original-caller-report format.

The checks establish internal consistency only. They do not authenticate a source,
renew a lease, refresh an image, establish model receipt or grant input authority.
A report fabricated consistently can pass; source SHA is identity, not provenance.
Independent task success stays unknown. No-attention output is not full evidence
review or comprehensive semantic validation. Full records remain accessible by path.

Offline tests cover successful actual Inkscape movement, recorded focus interruption,
and stale clock response. Success binds with no attention, interruption binds with
attention, stale response does not bind. Eight mutations reject mismatched request,
terminal/admission identity, source/submit sequence, missing continuation and timeout
status. A nested image diagnostic error surfaces at its exact source path.

Reproduce: `python3 research/live_control/probe_decision_receipt_v2.py`.
Evidence: `results/decision-receipt-v2-01/report.json`. V1 and measured v2 source bytes
are retained. No actual token/cost or latency benefit has been measured.

Next use this index plus the original image on one fresh private known-fixture task,
retaining all outcomes. Escalate attention to exact source details; do not replace
runtime admission with this index. Compare observed review burden descriptively
with the paged episode, not as a randomized or model-qualified speed comparison.
