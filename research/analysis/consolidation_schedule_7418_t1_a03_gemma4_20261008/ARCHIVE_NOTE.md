# T1 A03 source and outcome custody

This package preserves T1 A03 from exact branch
`research/8406-schedule-t1-a03-running-digest-20261008`, tip
`c16b3974b38fd3c3eb787b2744c5dbc27514003b`. T1 A03 is a separate allocation
from A01 and A02; their partial raw bytes are not inputs to A03.

`RUN_RECORD.json` and `STOP.md` record
`STOP_DUPLICATE_LOADED_RUNNER_IDENTITY`: one candidate invocation and model
request, no auditor invocation, and zero retries. The partial response is not
attributable to a single serving digest and is not scored. Do not resume, audit
as complete, or pool with another allocation. This disposition applies only
to T1 A03; it does not stop unrelated work.
