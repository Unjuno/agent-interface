# Same-task recovery pilot with terminal receipts — 2026-09-13

The second actual assistant recovery uses the same Inkscape fixture/seed, one-shot
replacement/restoration behavior, session21 controller and four task programs as
the first episode. interactive_recovery_v2 changes compact presentation to include
the review receipt. The assistant views initial and receipt-linked images, notices
the GUI X-coordinate mismatch, requests Escape/settle, recovers under a new explicit
lease, checks the moved object and saves. No controller-side file oracle is used.

Source sequence numbers vary with capture timing; lease timestamps also necessarily
vary. `recovery_boundary_report.py` verifies identical normalized task steps apart
from source sequence, exact final saved displacement, source manifests, receipt/image
references and 31 exact frame reconstructions across the two episodes.

| Metric | Earlier episode | Receipt episode |
|---|---:|---:|
| Saved target displacement | 24 px | 24 px |
| Accepted task programs | 4 | 4 |
| Explicit clock commands | 5 | 1 |
| First program acceptance → independent score | 97.400 s | 35.873 s |
| False terminal → recovery accepted | 59.717 s | 19.398 s |
| Reobserve terminal → recovery command received | 42.019 s | 11.139 s |
| Recovery terminal → save command received | 27.083 s | 9.023 s |
| Delivered JSON file bytes | 33,385 | 35,130 |

The new episode's individual programs take 0.357–0.892 s. Between-program gaps
remain 7.7–11.1 s; save terminal to scoring is another 5.5 s, including the wait for
the assistant's finish command. This locates most elapsed time outside accepted
local programs. It does not isolate model inference from image viewing, tool
transport, reasoning or orchestration. All endpoints use one runtime clock per run.

The assistant used terminal timestamps as historical clock anchors for the next
explicit lease, without extra clock queries after the first. No deadline was renewed
by a receipt: new programs retain independent admission checks and original leases.
Old/delayed receipts can still be too old for a next command and are not current-time
or image-freshness proof. The new episode did not need runtime log searches or guessed
PNG paths; these are observed workflow facts, not counts of all model/tool operations.

## Interpretation limits

This is one sequential pair with different assistant history/familiarity, changed
clock-query strategy and output budgets. It is **not randomized or counterbalanced**,
and cannot attribute the time difference to the receipt alone. Exact model inference
settings/tokens and transport overhead are not isolated. The receipt adds metadata;
the delivered JSON is larger, and bytes are not model image-token accounting.
No general speedup ratio, human-speed claim or global presentation promotion follows.

Both runs depend on the environment restoring the injected overlay. They do not
repair false patch identity or demonstrate recovery under persistent occlusion.
Y/size/transform are preserved and independent final score passes; that does not
make the initial local-goal event semantically correct.

Next use repeated order-controlled same-task comparisons and external boundary
telemetry before selecting a default. Keep causal timing endpoints, model-visible
cost and successful-task correctness together. Local motor micro-optimization alone
does not explain the remaining multi-second decision boundaries.
