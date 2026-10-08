# Issue #5760 T0 report

## H / T / D / C / U

- **H:** Conditioning on executed local actions can reverse the assignment-level final-outcome comparison for a fallback-bearing interface route; a complete assignment/exposure ledger detects the selection.
- **T:** Frozen deterministic two-fixture CPU table; one selection-reversal case and one null-balanced exposure control. Candidate, independent oracle, and raw-only audit were each invoked once. No runtime, GUI, model, game, input, GPU or Docker.
- **D:** The raw first audit output is `FAIL_T0_CONTRACT` (exit 1), so the preregistered PASS gate was not met. Keep the result at `HOLD_AUDIT_IMPLEMENTATION_MISMATCH`; do not rewrite or retry this allocation.
- **C:** Entirely authored finite synthetic fixtures; no randomization, causal attribution or real route/task observations.
- **U:** No evidence that an existing repository comparison is biased, no estimate of a live deployable-policy effect, and no #57/#59/runtime conclusion.

## Observed candidate and oracle outputs

Both independently executed calculators exited 0 and agreed exactly on both frozen fixtures.

- Selection fixture, all assigned rows: A success 1/2; B success 1; A mean total time 11/2; B mean total time 5. The A/local-only descriptive subset is 2/2 success and mean time 1, excluding both hard fallback failures and their time.
- Null fixture: both assigned success 1 and mean time 5; A/local-only subset also success 1 and mean time 5.
- Three preregistered mutations were rejected in the single auditor invocation: drop all fallback rows; relabel fallback as local; zero fallback total time.
- The auditor's first raw output reports two expected-value mismatches. Inspection identifies an auditor implementation bug: its computed summary includes `case_id`, while the hard-coded expected dictionaries omit that key. Thus the auditor marks both correct aggregates mismatched. The candidate/oracle result is retained, but no audit PASS is claimed.

## Integrity and scope

Frozen main: `2236be71c6bc97a6f52f3f5258484ee80e2c4a2f`. Exact fixture and source hashes are in `FREEZE.json`; invocation counts and exits in `EXECUTION.json`; first stdout bytes in the three `*.stdout.json` files. No retries. This method-only T0 does not establish randomized assignment, an ITT effect, IV identification, or empirical repository bias.

