# #5766 T0 allocation 02 — scoped method pass

Allocation `ORACLE-CHECK-5766-T0-20261001-02` is an explicit successor to allocation 01. It uses a new branch and path; the earlier `FAIL_T0_CONTRACT` and its exact artifacts remain unchanged. This version corrects the candidate interval gate and the auditor's frozen deck-hash lookup, and adds checks of the deck byte hash, canonical hash and reference-lock hash.

**Result: `PASS_METHOD_SCOPED`.** One pinned, network-disabled Docker candidate run completed four scenarios. One independent raw-only audit reported zero base errors and rejected all four preregistered mutations. Same-hash semantic drift produced in-deck score/reference disagreement and was held as `HOLD_ORACLE_DRIFT`; the meaning-preserving scorer/schema version change remained `ELIGIBLE_FOR_FURTHER_TASK_AUDIT`; the outside-coverage event remained `UNKNOWN_COVERAGE`. Nominal checks were also eligible only for further task audit.

This is synthetic finite method evidence. It does **not** establish that any real app/scorer drift occurred, that check fixtures are independently adjudicated in production, or that a live task oracle is valid. `H_PASS_SCOPED` was not claimed; T1 was not run. It does not close #12, #57 or #59.

## Reproduction and raw evidence

`FREEZE.json` and `PREREGISTRATION.md` bind the source, exact deck/reference, pinned Python image, allocation and decision gate. `RUN_MANIFEST.json`, exact command files, raw candidate output, independent audit output, stdout/stderr, exit codes and `SHA256SUMS` preserve the one-shot execution. Source and output checksums are validated before candidate/audit decisions; see each source file for fail-closed integrity gates.

No retries, model, GPU, GUI, live application, user data or OS input were involved. Docker ran with network disabled, read-only root, read-only source and separate output mount.

## H / T / D / C / U

- **H:** The frozen bracketed check deck detects in-deck semantic drift under unchanged scorer bytes without falsely rejecting an equivalent scorer/app version change, while out-of-coverage events remain UNKNOWN.
- **T:** Four finite constructed profiles over the same five frozen cases; candidate once, independent auditor once, four raw mutation checks.
- **D:** PASS_METHOD_SCOPED: zero audit base errors; drift held; version-equivalent control eligible; out-of-coverage UNKNOWN; all four mutations rejected.
- **C:** Fully deterministic synthetic fixture and stipulated semantic mappings; no real app or scorer change.
- **U:** Does not certify unseen semantics, real reference adjudication, live task outcomes or the repository's system-level objectives.
