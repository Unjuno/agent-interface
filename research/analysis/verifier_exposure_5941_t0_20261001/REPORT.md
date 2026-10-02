# Issue #5941 T0 — retained auditor-control HOLD

**Disposition: `HOLD_AUDITOR_NEGATIVE_CONTROL_NOOP`.** The one candidate run completed and the independent raw reconstruction reported zero row errors, but only 4/5 negative controls were effective. The fifth control (`forge_independence`) rewrote case 001's stored result to values it already had: its three votes are PASS/PASS/PASS, with the middle receipt's commitment invalid, so the independent set is already the two valid outer PASS receipts. This is a no-op mutation; the audit gate failed as required. Candidate and auditor were not rerun.

## H / T / D / C / U

- **H:** A count-only quorum can admit false PASS when a peer-exposed verifier copies an incorrect first-pass vote; independent quorum accounting should abstain unless two valid unexposed first-pass receipts agree.
- **T:** Frozen enumeration of eight verdict triples × four V2 exposure states × two commitment-validity states, plus omitted/forged-edge controls: 66 rows. Candidate once; separate raw-only auditor once.
- **D:** **HOLD**, not method PASS: 66 rows and independent reconstruction agree (`errors=[]`); the saved candidate shows 2 count-only false PASS cases and 0 exposure-scoped false PASS cases in this finite deck. But the `forge_independence` control was ineffective, so the required all-controls gate is unmet. These counts are candidate-derived descriptive diagnostics and are not promoted as audited scientific results.
- **C:** No-effect remains plausible under a different verdict distribution or an independently complete static-domain filter; the constructed copied-vote witness only establishes a logical possibility in this encoded case.
- **U:** Synthetic receipt metadata is trusted, only three voters/two verdicts are represented, and no model conformity, call-bound capture, GUI effect, cost, or deployed policy is tested.

## Execution evidence

Base main at the initial planning check: `2b899413d30fcee0ce97e7c69d83f7b2f69e89dd`; main advanced to `e1ebee404930401665c1fef64022b0ad3c373793` before publication. CPython standard-library Windows host, CPU only. Docker Desktop context existed but `docker info` timed out at 10 s; no container or shared resource was touched. No GPU, model, GUI, network, or input.

Pre-freeze construction: initial case-generator test failed before the formal freeze due to a tuple unpack mismatch; source was corrected, then 4/4 tests and `py_compile` passed. Frozen source SHA-256 values are in `FREEZE.json`. Post-freeze local hash checks matched all three source files. The exact candidate and audit commands, one-shot invocation counts, and exits are in `PROCESS.json`.

Candidate raw SHA-256: `24977104b75792bbaf977f80188eb86ab137c10d05ba063874d1688581190866`. Audit output SHA-256: `85d813d183b5533d1e74a2f667f3ddd3baaa7787f4cdd88406aae21584dff3d6`. All retained artifact hashes are listed in `SHA256SUMS`.

## Follow-up boundary

Do not repair and rerun within this allocation. If warranted, a successor should make every mutation control demonstrably change the expected raw-derived disposition, add a raw vote/edge-binding control that cannot accidentally preserve two independent supporters, then refreeze current main and all source bytes under a distinct allocation. This HOLD does not modify #5314 results or establish that language-model verifiers conform to exposed peers.
