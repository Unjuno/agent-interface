# A1 formal stop

Task: `LIVE-EXISTING-RUNTIME-READY-FENCE-20260917-001`.

A1 stopped on the outer container execution limit. It is permanently unpooled and will not be resumed, rerun, replaced or extended.

- complete first outcomes: `f00` endpoint_only = clock `timeout`; `f01` existing_ready_gate = clock `boundary`; both wrapper exit 0 and owner release verified neutral.
- consumed partial: `f02` created a fresh case directory and runtime evidence but no `case.json`; it is not a scientific row.
- unstarted: `f03`, `f04`, `f05`.
- A1 scientific disposition: NONE.
- A1 orchestration disposition: `STOPPED_OUTER_ORCHESTRATION_TIMEOUT`.

The next allocation may change only outer orchestration granularity: entirely fresh case IDs/seeds, one case per outer container invocation. Candidate, baseline, 300 ms clock timeout, source blobs and scientific decision gates remain unchanged.
