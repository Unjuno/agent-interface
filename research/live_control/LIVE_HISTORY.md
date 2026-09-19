# Live sequence mismatch and history assembly integration

A scripted private Inkscape run now isolates the sequence check that the previous
actual-use stale-boundary episode did not reach. This is a fault-injection test,
not a new assistant control episode or a successful rectangle-movement task.

The probe receives sequence 1, completes an observe-only program yielding sequence
2, then deliberately combines the latest received cursor with the old observation
records. That inconsistent batch is explicitly marked synthetic and never included
in the archive's list of real transport replies. The next clock reply matches the
probe's own request identity and reports sequence 2. The caller rejects the old
sequence-1 source before submitting its requested Right hold.

The probe then assembles **only actual received slices** through that clock using
`received_history_v1.assemble`, resolves the latest explicit image reference, and
checks sequence 2 before submitting a separate observe-only recovery program. That
program completes with sequence 3. This scripted decision is part of the test;
the history helper still returns `assembled_review_required` and never authorizes
input or automatically resubmits a rejected action.

## Evidence

`results/live-history-01` preserves the probe plan and source hashes before its
first query, runtime source manifest, original and synthetic batches separately,
all requests/replies, views/reports, assembled history, images and final saved SVG.
The probe plan is created after fixture launch but before any probe query; it is
not a pre-launch environment-registration claim.

`audit_live_history_v1.py` verifies source bytes, all 22 records across seven socket
exchanges, three exact AIT/PNG frames, own clock identity plus the explicit 1-vs-2
sequence difference, restoration of reversible views, and the assembled batch
actually used for recovery. Only `advance` and `recover-observe` are admitted;
both contain observe only and finish with verified release. No key/pointer input
admissions or held-key records occur. The bridge exits zero; the older desktop
entry does not provide structured per-child cleanup evidence.

The final SVG remains at x=50, y=50 with width=40 and height=30. Consequently the
independent movement-task score is **false**, as expected. Keep that score distinct
from the probe's successful mismatch/recovery assertions. No source or failed
result from prior experiments was altered.

## Limits and next step

This verifies a pre-clock sequence mismatch with a current receipt cursor. It does
not test content changes with the same sequence, concurrent producers after the
clock, transport loss, a gap, timeout reconciliation or automatic input retry.
Images were validated by the probe and audit, not presented as a new model-control
episode. There are no new model receipt, token, cost, human-tempo or speedup claims.

The remaining observed friction is the historical clock boundary: the caller
requires manual read-only progress when its first reply precedes its own echo.
A next implementation can bound that read-only progress and assemble every slice,
while retaining a review stop if observations change or any other boundary is
unresolved. It must not weaken identity matching or turn history assembly into
permission to repeat an action.

```sh
python3 research/live_control/audit_live_history_v1.py
```
