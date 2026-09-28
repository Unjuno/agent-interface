# Issue #5126 host-only counterexample recheck

**Disposition: `CONFIRMED_LINEAGE_ACCEPTANCE`; strict v2 contract remains unrun.**

## H / T / D / C / U

**H.** The #1839 v1 candidate, oracle and raw-only auditor continue to accept a
consistent row whose session, plan, actuation, owner and effect identifiers
are all a single whitespace-only string.

**T.** Freeze `FREEZE.json` pins current main `611962d3`, the immutable #1839
candidate/oracle/auditor/result and the present physical/scorer schema sources.
The one host construction probe copied the positive row in memory, replaced
those identifiers with `" "`, and checked the candidate, oracle and auditor
without writing into the historical #1839 directory. It also enumerated the
source-record keys carried by the fixture.

**D.** The probe reproduced the failure: candidate and oracle both returned
`PHYSICAL_ACTUATION_SCOPED` and `TASK_EFFECT_SCOPED`; the raw-only auditor
returned `PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED`, `errors=[]`. The current
flattened down/up and task-effect records contain no `event_id`,
`event_sequence`, or `source_event_ref`. The scorer source does generate a
per-clock `event_sequence`, but #1839's flattened task-effect schema drops it.
This confirms the malformed-lineage defect and identifies a source identity
gap for duplicate-event rejection. The inherited `formal_allocations: 1` field
in the v1 auditor describes the historical v1 result; this host probe launched
zero formal allocations.

**C.** This is a synthetic host-only construction check, not the #5126 strict
candidate/oracle/auditor experiment. No live events, model, GUI, X11, game,
input, GPU or container were used. The historical #1839 result and auditor
files were not edited.

**U.** It remains unproven whether the full raw runtime envelopes retain stable
physical-event references that the flattened contract omitted. The required
offline-container v2 experiment has not run because the shared CPU-container
slot has not been assigned. No #5126 contract pass or promotion is claimed.

## Reproduction

Frozen command: `python -B research/doom/task_effect_lineage_5126_v1/probe_v1_counterexample.py`

Environment: Windows host, CPython 3.11.9. Exit code 0 means the known
counterexample was reproduced; it does not mean the contract passed. Raw
stdout is `host_probe_output.json`; hashes are in `EXECUTION.json`.
