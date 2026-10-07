# Result — GUI-REVERSIBILITY-7949-JOURNAL-A01

## Disposition

**`PASS_JOURNAL_STATE_RECONCILIATION_SCOPED`**, with a material scope qualification: the complete-disjoint-write case emitted the frozen `PROPOSE_COMPENSATION` proposal and bound revision 1 while preserving the external value, but the certificate baseline agent value (`original`) was already equal to the current agent value (`original`). Therefore the proposed restore was idempotent/no-op; this allocation did **not** demonstrate changing a modified agent-owned field back to its baseline. The result supports finite journal/state mismatch detection and proposal-field scoping, not actual recovery effectiveness.

## Result

| Case | Candidate disposition | Independent audit |
|---|---|---|
| baseline | `NO_CHANGE` | reconstructed |
| complete disjoint write | `PROPOSE_COMPENSATION`; restore `agent_value=original`, preserve `external_value=external-new`, bind revision 1 | reconstructed; restore value was already current |
| same-field write | `UNKNOWN` | reconstructed |
| revision advanced, journal row missing | `UNKNOWN` | reconstructed |
| journal sequence gap | `UNKNOWN` | reconstructed |
| journal/state mismatch | `UNKNOWN` | reconstructed |

The auditor independently opened and queried all six SQLite DBs read-only, compared each result with the separate observer snapshot, reconstructed all six decisions, and reported zero errors. Four candidate/output mutation controls and four raw-observation mutation controls were all rejected (8/8). Candidate and auditor both exited 0. No compensation proposal was applied; authority/external actions=0.

## Interpretation

For this authored finite SQLite fixture, observed revision plus a contiguous journal matching current field values caused malformed/missing evidence to fail closed as UNKNOWN. The one internally consistent disjoint event yielded a proposal limited to the certificate-owned field and preserved the observed external field. The favorable single-transaction/store-local setup does not test non-SQLite writes, multiple files, dishonest observers, or recovery effects.

The no-op restore limitation is retained as observed; it is not repaired by editing the frozen case or report. A distinct fresh allocation would need `current agent_value != certificate baseline` before the external write, then independently assert that a simulated bounded application of the proposal changes only the agent field while preserving the external value and revision binding. This is a new hypothesis rung, not a rerun of A01.

## Scope

Native macOS Python 3.14.5 standard-library processes, arm64; no container isolation because the predeclared OrbStack image inventory query failed. No GUI, model, network, third-party dependency, host input, privilege, real artifact-store integration, actual compensation, safety or product claim. See `RUN_RECORD.md`, `POST_RUN_QUALIFICATION.md`, and `FINAL_SHA256SUMS.txt`.
