# Recovery status — allocation v1

Disposition: `STOP_BEFORE_CONTAINER_OR_TRAINING`.

This directory preserves the seven frozen v1 source/freeze files unchanged from
the original branch. The one host wrapper invocation stopped during the
freeze-schema preflight with `KeyError: 'environment'` (exit 1). Training and
auditor containers, optimizer updates, and model evaluations were all zero;
there were no retries. This is a harness/schema STOP, not a scientific result.

The v2 successor archive records the same v1 STOP at
`research/experiments/needle_online_snapshot_cadence_4621_v2/provenance/PREDECESSOR_STOP.json`.
The original detailed STOP.json was reported as retained in the worker task
workspace; it was not available in the branch and is not reconstructed here.
No formal experiment was rerun.

The v2 successor is separately archived at
`research/experiments/needle_online_snapshot_cadence_4621_v2/`; its findings
must not be attributed to this v1 allocation.
