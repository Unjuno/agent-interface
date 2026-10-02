# Sole formal run — HOLD_AUDIT_INTEGRITY

Issue #4899; frozen allocation `needle-role-router-online-lora-replay-20260927-v1`. Source and seeds were not changed after freeze. Formal seeds 736211, 736311 and 736411 ran once each across four paired arms in the pinned CPU Docker image; trainer exit 0, 1,611,168 raw bytes, raw SHA-256 `7ff93c67a4bc8e9f864511f1b89bf4fe2109287fd359927fee51de345c10188b`. The formal receipt binds the pinned image/platform, exact argv, stdout/stderr, raw bytes/hash, one orchestration and zero retries. A distinct Docker invocation audited the raw once and exited 2.

## H / T / D / C / U

- **H:** Role-routed separate A/B skills would retain A while acquiring B and outperform shared online and fixed-replay packages.
- **T:** Exact frozen four-arm study and gates in the parent `FREEZE.json` / `PREREGISTRATION.md`; no tuning, retries or replacements.
- **D:** Registered result is **`HOLD_AUDIT_INTEGRITY`**, not PASS and not an upgradeable raw-only scientific FAIL. The auditor found exactly three errors: `736211:base_row_indices:digest`, `736311:base_row_indices:digest`, `736411:base_row_indices:digest`. It reconstructed all 192 arm-arrival checkpoints; all other base/split/model/optimizer/prediction/route checks were error-free.
- **Observed quality (descriptive under HOLD):** every separate-skill seed ended A/B=1.000/1.000. Shared B-only and routed-shared ended A/B=0/1 on all seeds. A-replay ended 1.000/0.285 (736211), 0.465/0.539 (736311), and 0.277/0.770 (736411). Maximum measured optimizer step across the four arms per seed was 1.586, 0.593 and 0.698 ms respectively; each is below 60 ms. However, seed 736211's A-replay A=1.000 ties the separate arm, so the preregistered +0.10-A-over-each-shared-arm gate is demonstrably missed on that seed. Because the registered auditor has an integrity error, retain HOLD as the formal disposition; do not relabel it PASS or rewrite the frozen audit.
- **C:** Auditor defect: `runner.run_seed` hashes the declared dataset fields but intentionally does not include `base_row_indices` in `dataset_sha256`; the auditor loops over its broader `fields` tuple and incorrectly demands a digest for that optimizer schedule. The schedule itself is independently regenerated and compared exactly without error. This is an auditor expectation mismatch, not a measured model/raw mismatch. No repaired audit or second trainer run was performed.
- **U:** One host, one pinned CPU image, three synthetic seeds with explicit role feature, small model. No natural-language routing, live Needle interaction, task utility, transfer, real-time end-to-end latency, production learning, or action authority.

## Preserved artifacts

- `raw/formal_result.json`: 1,611,168 bytes; SHA-256 `7ff93c67a4bc8e9f864511f1b89bf4fe2109287fd359927fee51de345c10188b`.
- `FORMAL_INVOCATION.json`: SHA-256 `061565dbe4a0c6ab35099d772a13346f875c13012c262e29d2faad3abafdb8f4`.
- `audit/AUDIT.json`: SHA-256 `028b67b1db33a2c09798025156539c084fc31d7ccf2e35dbfac4fb2a67942c1b`.
- `audit/AUDIT_INVOCATION.json`: SHA-256 `fbed8920efa81268abce8c87c944b41b3c7fbf13a045d954271f8f5e62b56a12`.
- All exact trainer/auditor stdout and stderr are retained beside their receipts.

The next valid step is a new successor allocation fixing the auditor's field/hash contract and preregistering a causally narrower follow-up for the A-replay tie. This frozen allocation and its formal raw/audit remain immutable.
