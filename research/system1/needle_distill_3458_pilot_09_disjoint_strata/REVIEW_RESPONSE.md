# PR #4481 review revalidation (post-hoc; no formal rerun)

This supplement answers the two review observations without editing the frozen runner, auditor, preregistration, FREEZE, or formal raw result. `review_revalidation.py` reads the retained gzip payload and audit summary, checks the frozen SHA-256 manifest and issue-contract binding, recomputes paired recall lifts and the per-seed shifted-quality gate, and writes `REVIEW_REVALIDATION.json`. It does not import the original runner/auditor and performs no training, replay, seed replacement, or scientific rerun.

## Mean lift versus per-seed lift

The public decision rule specifies mean paired CORRECT-recall lift ≥0.10; the frozen auditor also requires every individual lift ≥0.10. That implementation is more restrictive in general. On this retained result, however, the individual lifts are 0.9974968711, 0.6180469716, and 0.7420118343, and their mean is 0.7858518923. Both formulations pass the lift gate for these observations. Seed 3492 independently fails the preregistered shifted-quality gate (accepted accuracy 0.9176072235 <0.95; CORRECT recall 0.7420118343 <0.95), and the treatment recall standard deviation is 0.1216167876 >0.05. The decision remains `FAIL_DISJOINT_STRATA_AUGMENTATION`; the generic auditor logic issue does not change this allocation's outcome. The frozen auditor is preserved verbatim.

## Frozen source identity

All ten source files listed by `FREEZE.json` match their frozen SHA-256 values in the submitted tree. Their Git blob identities also match the corresponding files read back from PR #4481's head. The original evidence branch records the freeze commit `614a9d2e5f40b20b87f078e7fe44ce5740705902` (2026-09-26 13:46:12Z), then the result/audit commit `db2212a9ca1739f40bbc0730e2d37eb805abeeb1` (13:54:51Z), followed by the compressed exact-raw commit `d25b29ad8abea58e8efc0ff6c869c7513551b59c` (13:56:16Z). The frozen source tree therefore predates the public result commits.

Limitation retained: the formal payload itself does not contain a runtime source digest. The committed freeze chronology and source hashes corroborate which source tree was intended, but do not independently attest the exact mounted bytes at process start. This limitation must remain visible; this supplement does not upgrade the result to runtime attestation.

## Local verification

The post-hoc checker completed in the pinned local `needle-pilot05:local` Linux/amd64 CPU container with network disabled, read-only root/source, 1 CPU, 2 GiB memory, 64 pids, and 64 MiB tmpfs. It returned exit 0 with `errors=[]`, verified the raw SHA-256 `ee680b543073c89539a9dc131c0b4e24ca09f82d19054000106ef4630c8a1706`, and reproduced the unchanged FAIL disposition. This is evidence-only revalidation, not a new training allocation.
