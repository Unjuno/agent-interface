# Issue #6367 T0 freeze

- Allocation: `EXPOSED-SUCCESS-AUDIT-6367-T0-20261002-01`
- Base main: `c6e4c7ad413bcc9605ab5bf00df0eaa4ac7ba560`
- Branch: `research/exposed-success-audit-6367-t0-20261002`
- Scope: deterministic synthetic event ledger only; Ubuntu 24.04.4 / WSL2 / Python 3.12.3; no model, GUI, user input, GPU, network, Docker Desktop, or container.
- Candidate/auditor calls: one each; retries: zero.
- Candidate command: `python3 -B candidate.py fixtures results`
- Auditor command, only after candidate exit 0: `python3 -B auditor.py fixtures results results/audit.json`
- Failure boundary: a nonzero candidate exit is retained and terminates this allocation; do not invoke the auditor or rerun the candidate. A nonzero auditor exit is retained as FAIL_AUDIT; no repair/re-audit in this allocation.
- WSLc rationale: this fixture has no external service, filesystem isolation, or resource-enforcement dependency; the dedicated WSLc session was not used while another WSLc audit lane was active. Native WSL is the bounded CPU execution environment.

## Frozen source/input SHA-256

These exact digests were checked after construction tests and before the single candidate invocation. `SHA256SUMS` also covers this freeze and the construction record.

| Path | SHA-256 |
| --- | --- |
| `candidate.py` | `d6f49d392cacbd7d2edbce8de923b9857188591aab5f7bc63a418f2611500268` |
| `auditor.py` | `876212bfd0b56177c08f2cc38fefdd21cba472527e7598eb56aea0ddae2cd50a` |
| `tests/test_candidate.py` | `139d774e13b99278b3824b5f8160201b3a40a55b8229ec15927da046d9688c06` |
| `tests/test_auditor.py` | `30ee063083804ca97998cd1d0c3b006e05c283ae8f98f6c05b98454bb043f198` |
| `fixtures/primary.json` | `6b46db2d58a4ecfdd6214bcb9779e6447d34fe448b6dc58706b7579a0a806f0d` |
| `fixtures/selection_trap.json` | `e74130346924f40d7b51bcb80731e9c8cb0cb49df1e4d6caf407a8a73481a067` |

## H/T/D/C/U

- **H:** Keeping every exogenously assigned offer in the denominator prevents post-policy selection from turning a null all-offer effect into a false adaptation benefit.
- **T:** Two immutable JSON fixtures: eight primary control opportunities spanning benefit, null, suppression, challenge shift, stale cue, missing independent effect, missing qualified occupancy, and unsafe release; plus four matched selection-trap opportunities. A small candidate classifies each arm, and a separately implemented standard-library auditor reconstructs the denominators, effects, freshness, occupancy, release, and safety findings from raw fixture bytes.
- **Construction gate:** Run the 11-unit-test suite normally and with `-O`, byte-compile both implementation files, and verify JSON parse before freezing hashes. Construction results do not count as the formal allocation.
- **D:** `PASS_METHOD_ONLY` only if literal expected cases and an independent audit agree, missing rows remain in assigned denominators, the selection trap yields a 2/4 vs 2/4 null despite 2/2 adaptive-triggered successes, the stale trigger and challenge shift are not credited, and unsafe release yields `FAIL_SAFETY`. Any discrepancy is retained as FAIL/STOP; no repair-and-retry of the frozen candidate.
- **C:** Synthetic receipts establish only the ledger's decision behavior. They do not validate a real exogenous challenge generator, live controller, task effect, physical occupancy measurement, statistical estimator, runtime safety, or user benefit.
- **U:** No causal or live-control inference. Post-policy occupancy/adaptation counts are descriptive only; the primary contrast is the all-offer policy-assignment contrast. Any absent evidence yields UNKNOWN/HOLD, never zero.

The fixture schedule, candidate source, expected outputs, auditor source, and exact commands must be hashed and frozen before the single candidate invocation. Candidate output and audit output are separate immutable files. The auditor must not import or invoke candidate code.
