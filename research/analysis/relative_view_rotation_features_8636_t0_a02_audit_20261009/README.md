# Issue #8636 T0 A02 retained-raw audit-only successor

This successor audits the exact A02 candidate archive after its first independent auditor stopped before a summary. It does not invoke the A02 candidate, rerun the A02 auditor, alter A01/A02 artifacts, or convert A02's `HOLD_UNCERTAIN` into a preregistered scientific result.

## H / T / D / C / U

- **H:** A separately versioned raw-only reconstruction that models the frozen runner's actual observation path can either reproduce all 360 assigned trials, actions, feature values, statuses, terminal outcomes and releases from the retained archive, or locate a concrete inconsistency. The previously failed auditor's pose-reference assumption may not match the runner because landmark detection occurs before arm dispatch.
- **T:** One read-only audit of the retained A02 archive (`SHA-256 a9004e4e84dadcdd6595dd738bec77e69de84e5b51767985129f968649ddeeb9`) using a separately versioned auditor, CPython 3.12.13, and no candidate/model/GUI/runtime invocation. Verify all archived frame hashes, reconstruct all event rows and terminal scorer records, check the 120-seed-condition groups and 360 trial arms, and run frozen in-memory corruption controls. Candidate output and predecessor files remain immutable.
- **D:** `PASS_AUDIT_ONLY_SCOPED` only if archive identity, all 360 trials and all observation/release records reconstruct, all source/transition/status/score checks pass, and every mutation control is rejected. Any discrepancy is `FAIL_AUDIT_ONLY_MISMATCH`; input/source/runner failure is `STOP_PROVENANCE`. Regardless of audit-only outcome, A02 remains `HOLD_UNCERTAIN` because its original auditor failed and its formal interpreter was not pinned to the recorded environment.
- **C:** The candidate output may be internally consistent while the original auditor had a faulty expectation; alternatively the artifact may expose a candidate or provenance defect. The audit cannot recover the missing original auditor exit success or make A02's environment match its freeze.
- **U:** This is only a post-run reconstruction of one synthetic archive. It does not establish the feature hypothesis, real GUI applicability, task success, safety, latency, or portability. It does not supersede the A02 first outcome.

No container is used: this is bounded deterministic parsing and reconstruction of retained bytes, with no OS/container semantics under test. The single audit uses CPython 3.12.13 to match A02's recorded freeze runtime; this does not change A02's actual CPython 3.14.5 execution fact.
