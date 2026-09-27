# Rule-reconciliation result — Issue #4597

Allocation: `confidence-trajectory-4597-rule-reconciliation-20260927-01`.
Disposition: **CORRECTION_CONFIRMED — predecessor velocity metric not spec-conformant**.

## H/T/D/C/U

- **H:** Correcting the predecessor's undeclared `v2 >= 0` condition on its current-only positive branch changes the six high-confidence/falling rows and reduces the reported velocity gain.
- **T:** One frozen reanalysis of the immutable predecessor's 84 raw inputs, using OrbStack/Docker Engine 29.4.0, pinned `linux/arm64` image `sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`, Python stdlib, `--network none`, `--read-only`, read-only source and separate output mount. No new observations, GUI, model, user data, or action authority.
- **D:** Source SHA-256 matched the frozen predecessor raw hash; 84 rows replayed. Six and only six velocity decisions differ from predecessor output, all `high_confidence_falling_yield-00` through `-05`. After PR review, the audit was strengthened to independently reconstruct every decision and aggregate directly from the pinned raw input; 5 audit checks report no errors and 2 corruption regressions are rejected. The post-formal validation suite has 6 passing tests. Container exit 0, network `none`, read-only root `true`.
- **C:** This corrects a specification/implementation mismatch in the predecessor, not an estimate of real-world event rates. The authored synthetic corpus and same-author audit remain limitations.
- **U:** Synthetic and authority-neutral only. No real-model, task-success, generalization, safety, or runtime-promotion conclusion follows.

## Corrected comparison

| Policy | Predecessor reported correct / 84 | Frozen-spec correct / 84 | Predecessor false ACTION | Frozen-spec false ACTION |
|---|---:|---:|---:|---:|
| CURRENT_ONLY | 66 | 66 | 12 | 12 |
| LEVEL_PLUS_VELOCITY | 78 | 72 | 6 | 12 |

The six changed inputs all have `p2 >= 0.75` with a negative latest velocity and truth `YIELD`. The frozen rule preserves the current-only positive branch, so those rows become ACTION and are false executable decisions. The predecessor's 78/84 and six-false-ACTION velocity result must not be interpreted as following its frozen plan. Corrected velocity still scores 72/84 versus current-only 66/84 on this authored corpus, but both have 12 false ACTION; this narrow difference does not validate trajectory use beyond this dataset.

## Formal execution and retained failures

The sole successful formal container invocation ran the frozen reanalysis, the original 3 unit tests, and the then-current audit. Container ID: `b2ae90b58618790ab9900aabd77c657f8fe1de7edce45d685663213ac5614059`; exit 0; network none; read-only root true. During subsequent PR review, a P2 finding correctly noted that the first audit only checked runner-produced aggregate fields and did not independently reconstruct the changed rows from raw input. Therefore the initial audit's `errors=[]` is not treated as adequate independent validation. Without rerunning or changing the formal reanalysis, a post-formal audit implementation was added that reads and hashes the pinned raw artifact, recomputes every frozen decision and metric in separate code, compares every changed-row record, and rejects altered-input-hash and reversed-decision controls. The strengthened suite was then validated locally and in a separate read-only container audit invocation (container `b0a79023f3d3fd77fcf0e019283360480b1a1ffca3bceaa1e1bccccdc20428d3`); its output is retained below.

One earlier Docker start attempt failed before the container process began because the host bind source was four parent directories above the checkout rather than the repository root. It did not read inputs or execute tests/reanalysis. Docker retained that failed container in `created` state with exit 128; its error and identity are in `failed_container.json`. The corrected mount was used for the sole formal invocation, whose receipt is `container-02.cid`.

Preformal construction preview also observed the same six differences and was excluded from formal output; it did not alter source or thresholds. The predecessor raw artifact remains untouched and is only read through a read-only mount.

## Integrity

Frozen plan and formal-runner digests are in `FREEZE.sha256`; the strengthened post-formal auditor is a review-driven validation addition and does not alter the frozen reanalysis result. Successful formal reanalysis JSON is `results/formal-01/reanalysis/reanalysis.json`; its SHA-256 is `93a9a13bde3ecf681e24dd1c9cbfff3d939efe66a8c6b48ec49623de5078059f`. The post-formal audit command and test output are retained in `results/formal-01/post-audit-ci.txt`, with the Docker receipt in `post-audit-container.json`. All package hashes are in `results/RESULT_SHA256SUMS`.
