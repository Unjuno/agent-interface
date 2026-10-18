# Unregistered duplicate execution archive — #7949

## Disposition

**`STOP_DUPLICATE_ALLOCATION_ALREADY_CONSUMED`**. The full GitHub Issue #8300 timeline contains an earlier freeze and formal result for this exact allocation ID (`GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007`), posted before this local execution. The duplicate candidate/auditor payloads below are preserved only as custody evidence and are not a second scientific result. Do not combine them with, replace, or reinterpret the original A01 result.

The duplicate payload's own disjoint-write case proposed the bounded field/value and bound revision 1 while preserving the external value, but its restore was idempotent/no-op because the current agent value already equaled the certificate baseline. This is only an additional limitation in the duplicate archive, not a correction to the original A01 result.

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
