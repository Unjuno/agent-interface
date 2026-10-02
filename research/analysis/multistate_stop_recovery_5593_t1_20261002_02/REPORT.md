# Formal report — roster-bound multistate method check

## Disposition

`PASS_METHOD_MULTISTATE_ROSTER_SCOPED` for the frozen synthetic six-episode fixture. Candidate=1 invocation / exit 0; separate raw-only auditor=1 invocation / exit 0; retries=0. Auditor errors=0. Construction tests=11/11; `py_compile` passed.

## Result

The candidate emitted six launched episodes across ticks 0–5. The independent auditor matched fixture IDs exactly against a separately frozen N=6 roster, independently reconstructed every event and tick, and found occupancy mass exactly six at each tick. `SAFE_STOP` remained nonterminal through recovery, including one repeated `RECOVERING → SAFE_STOP → RECOVERING` path. `TERMINAL_STOP`, `VERIFIED_SUCCESS`, `VERIFIED_FAILURE`, and `CENSORED` remained distinguishable.

All six frozen corruption controls were rejected: omitted episode against roster; omitted recovery; recovery after absorbing success; unknown status; duplicate ID; and output denominator loss. Machine audit result records `errors=[]` and the exact control names.

## Integrity / execution

- Main at freeze: `3d33fe482ad55e99943f2c7b40e92c685c3bf92a`.
- Image: local pinned ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Construction: 11 tests pass and Python compilation passes before formal execution.
- Candidate and auditor ran in distinct fresh `--network none` containers, each with 1 CPU, 256 MiB, 64 PIDs, a read-only source/data mount, and separate disposable output mount.
- Formal outputs and their digests are retained in `candidate_result.json`, `audit_result.json`, and `SHA256SUMS`.
- Predecessor T0 `METHOD_FAIL_AUDIT` remains intact and is explicitly linked. No T0 formal rerun occurred.

## H/T/D/C/U boundary

This verifies only exact finite-state ledger bookkeeping under a hand-authored fixture and roster. It does not estimate real transition probabilities or censoring, show empirical task recovery benefit, establish causal effects, or validate any runtime, model, GUI, safety, human-tempo, or product behavior. An actual eligible prospective cohort remains necessary for empirical #5593 claims.
