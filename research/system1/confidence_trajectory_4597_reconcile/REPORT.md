# Rule-reconciliation result — Issue #4597

Allocation: `confidence-trajectory-4597-rule-reconciliation-20260927-01`.
Disposition: **CORRECTION_CONFIRMED — predecessor velocity metric not spec-conformant**.

## H/T/D/C/U

- **H:** Correcting the predecessor's undeclared `v2 >= 0` condition on its current-only positive branch changes the six high-confidence/falling rows and reduces the reported velocity gain.
- **T:** One frozen reanalysis of the immutable predecessor's 84 raw inputs, using OrbStack/Docker Engine 29.4.0, pinned `linux/arm64` image `sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`, Python stdlib, `--network none`, `--read-only`, read-only source and separate output mount. No new observations, GUI, model, user data, or action authority.
- **D:** Source SHA-256 matched the frozen predecessor raw hash; 84 rows replayed. Six and only six velocity decisions differ from predecessor output, all `high_confidence_falling_yield-00` through `-05`. Independent audit: 5 checks, no errors. Local/container unit tests: 3 passed. Container exit 0, network `none`, read-only root `true`.
- **C:** This corrects a specification/implementation mismatch in the predecessor, not an estimate of real-world event rates. The authored synthetic corpus and same-author audit remain limitations.
- **U:** Synthetic and authority-neutral only. No real-model, task-success, generalization, safety, or runtime-promotion conclusion follows.

## Corrected comparison

| Policy | Predecessor reported correct / 84 | Frozen-spec correct / 84 | Predecessor false ACTION | Frozen-spec false ACTION |
|---|---:|---:|---:|---:|
| CURRENT_ONLY | 66 | 66 | 12 | 12 |
| LEVEL_PLUS_VELOCITY | 78 | 72 | 6 | 12 |

The six changed inputs all have `p2 >= 0.75` with a negative latest velocity and truth `YIELD`. The frozen rule preserves the current-only positive branch, so those rows become ACTION and are false executable decisions. The predecessor's 78/84 and six-false-ACTION velocity result must not be interpreted as following its frozen plan. Corrected velocity still scores 72/84 versus current-only 66/84 on this authored corpus, but both have 12 false ACTION; this narrow difference does not validate trajectory use beyond this dataset.

## Formal execution and retained failures

The sole successful formal container invocation ran the frozen reanalysis, 3 unit tests, and independent audit. Container ID: `b2ae90b58618790ab9900aabd77c657f8fe1de7edce45d685663213ac5614059`; exit 0; network none; read-only root true. The exact image and constraints are in `FREEZE.json` and the Docker receipt.

One earlier Docker start attempt failed before the container process began because the host bind source was four parent directories above the checkout rather than the repository root. It did not read inputs or execute tests/reanalysis. Docker retained that failed container in `created` state with exit 128; its error and identity are in `failed_container.json`. The corrected mount was used for the sole formal invocation, whose receipt is `container-02.cid`.

Preformal construction preview also observed the same six differences and was excluded from formal output; it did not alter source or thresholds. The predecessor raw artifact remains untouched and is only read through a read-only mount.

## Integrity

Frozen source/plan digests are in `FREEZE.sha256`. Successful formal reanalysis JSON is `results/formal-01/reanalysis/reanalysis.json`; its SHA-256 is `93a9a13bde3ecf681e24dd1c9cbfff3d939efe66a8c6b48ec49623de5078059f`. All package hashes are in `results/RESULT_SHA256SUMS`.
