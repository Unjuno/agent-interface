# Issue #5370 waiter-deadline rung — raw-only audit v2

This is a separately versioned **audit-only successor** for the immutable raw
from allocation `G5370-PRIORITY-INHERITANCE-T5-20261001-01`. It does not rerun
the candidate or change its FREEZE, runner, raw output, or audit-v1 STOP.

## H/T/D/C/U

- **H:** An independent raw-only audit that accounts for stale-abstention ticks
  separately from scheduled execution events will reconcile the exact seven-row
  raw output against the frozen waiter-order criteria without false schedule
  gaps, while still rejecting malformed outcomes and corrupted controls.
- **T:** Freeze a new auditor and eight construction/mutation tests against
  current-main provenance and raw SHA-256
  `9841ce4220a7ba3a6c77cbd3c69efc794c8555f67bf65511d78f7c881641b3ca`.
  Run the construction suite before freeze, then invoke the auditor exactly
  once on that retained raw. Do not invoke the candidate again.
- **D:** PASS only if all seven unique policy rows reconcile; completed jobs
  meet deadlines; stale abstentions account for a one-tick logical slot;
  schedule + abstention slots form a contiguous timeline; holder and medium
  work, release tick and two-tick inheritance budget match; equal-deadline
  ordering remains FIFO-compatible; unauthenticated urgency is rejected; and
  the independent audit emits zero errors. Otherwise preserve a v2 audit STOP.
- **C:** This is an audit of one deterministic synthetic raw output. The raw
  producer's source is not imported; no scheduler implementation or runtime is
  exercised.
- **U:** No live scheduling, GPU/Docker, cryptography, production fairness,
  stochastic latency, starvation, or task-quality claim. Even a PASS only
  resolves auditability of this finite trace, not broad scheduler efficacy.

Audit-v1 remains immutable and failed. The likely defect is specifically that
it compared an empty `set` of IDs to `{}` and required every service tick to be
present in `schedule`, although stale abstentions are represented separately
by `observed_at`. Audit-v2 tests those boundaries without weakening the
expected results or importing the candidate.

