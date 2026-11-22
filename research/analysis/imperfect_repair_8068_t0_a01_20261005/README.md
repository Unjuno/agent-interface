# Issue #8068 — imperfect-repair method check T0 A01

Status: `HOST_METHOD_PASS_SCOPED; WSLC_CANDIDATE_STOP`. This is a synthetic
finite-state method result only. The one WSLc candidate invocation failed before
writing output because the candidate wrote beside its read-only source. It was
not retried. The one WSLc audit invocation independently reconstructed the
already-retained host candidate raw. Therefore this packet does **not** claim a
WSLc candidate pass or a completed in-container allocation.

## H / T / D / C / U

**H:** Under equal one-tick pre-repair exposure and a two-tick recurrence
horizon, the finite oracle distinguishes perfect renewal, minimal repair, and
an intermediate partial-repair operator, while retaining censoring and the
initiating fault label.

**T:** Enumerate four authored integer states by three typed operators (12
cells), then independently reconstruct transitions, recurrence, censoring,
coverage, and summaries from raw JSON. Three mutation controls probe omission
of a censored row, erasure of a censor label, and operator relabeling.

**D:** `PASS_METHOD_SCOPED` requires all 12 cells to match and all three
mutations to be rejected. Host candidate and raw auditor met the finite method
gate; WSLc candidate execution did not.

**C:** This authored deterministic toy system is expected to distinguish its
own operators; no natural recurrence law or predictive value is presumed.

**U:** No interface recovery traces, independent fault taxonomy, empirical
exposure, intervention assignment, calibrated probabilities, GUI/runtime
behavior, or policy value are represented. No reset/retry authority follows.

## Frozen setup and results

- Source base: `d5afff08116722563a016d4e1eb1d63b7d1ccd23`.
- Protocol: `protocol.json`; 1 host candidate run, 1 host raw audit, 0 retries.
- Host normal and `python -O` tests: 4/4 each. The candidate wrote 12 rows once;
  the independent auditor reconstructed 12/12 with zero errors. Three mutation
  controls were rejected. These are method-construction checks, not empirical
  repair evidence.
- WSLc version 3.0.1.0, cached `python:3.12-slim` image ID
  `9e87977b8678`, no network, one CPU, requested memory 512 MiB. The kernel
  reported that cgroup/swap memory enforcement is unavailable; no enforcement
  claim is made.
- WSLc read-only-source unit suite: 4/4 PASS.
- WSLc candidate: one invocation STOPped with `OSError: [Errno 30] Read-only
  file system: '/src/candidate_raw.json'`. Exact command and output are in
  `WSLC_RUNS.md`. Candidate 0 output written in WSLc; no retry.
- WSLc independent auditor: one invocation over the pre-existing host raw,
  12/12 rows, zero errors. This does not repair the candidate STOP or establish
  a full WSLc allocation.

## Scope

The finite fixture confirms only that this authored enumerator and independent
integer oracle can distinguish their planted transitions and censoring on 12
cells. It does not test recurrence prediction, held-out data, causal repair
effect, renewal assumptions in a real interface, escalation policy, or any
product behavior. A later WSLc execution would require a separately versioned
successor allocation with an explicit writable `/out` contract; this failed
allocation is preserved unchanged.
