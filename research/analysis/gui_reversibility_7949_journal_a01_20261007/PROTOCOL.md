# Issue #8300: journal/state reconciliation probe

## H / T / D / C / U

- **H:** A transaction-coupled, gap-free journal that replays exactly to the committed artifact revision/state can distinguish a disjoint external write from stale evidence. In that case an agent may compensate only its owned field. Missing, discontinuous, or state-inconsistent evidence must produce UNKNOWN and no write.
- **T:** Six SQLite cases: baseline; complete disjoint `y` write; same-field `x` write; revision advance without a journal row; journal sequence gap; journal value tampering.
- **D:** `PASS_JOURNAL_STATE_RECONCILIATION_SCOPED` only if the independent auditor accepts all six raw records, the baseline/disjoint cases compensate only `x`, and all four unsafe cases remain unchanged with UNKNOWN. Otherwise `FAIL` or `HOLD` per the discrepancy; no extrapolation to GUI, multi-process scheduling beyond this probe, or production authority.
- **C:** Standard-library Python/SQLite; six fixed cases; one candidate process per case and one independent audit process total; no retries. Local macOS process isolation only; OrbStack image-store preflight was unavailable, so no container-isolation claim.
- **U:** No production implementation claim, no real application/GUI claim, no concurrency stress claim, and no authority/permission claim. This probes a synthetic model only.

The writer is a separate subprocess; the observer is a separate read-only subprocess; the candidate only decides from serialized observations; the auditor independently re-reads SQLite snapshots and does not import candidate or writer code. Artifacts preserve pre/external/final database states. A PASS is scoped to these deterministic cases and this exact source freeze.
