# Issue #5841 T0 — same-cohort negative-control endpoints

## Disposition

**`PASS_METHOD_SCOPED` (host-only synthetic method evidence).** The frozen method detects route-dependent missingness and foreign task joins behind favorable complete-case primary contrasts, separates check-standard-visible endpoint export drift, and classifies a real sentinel change as non-compensable `COLLATERAL_FAIL`. Clean-null and true-primary-benefit controls do not trigger a false ascertainment alarm. This is not evidence that a particular negative control is valid in a real GUI-agent cohort.

## Frozen design and execution

- Issue: [#5841](https://github.com/Unjuno/agent-interface/issues/5841), T0 only; no participant, live GUI, model, or new route-comparison allocation.
- Allocation label: `ISSUE5841-T0-HOST-20261001-01`.
- Frozen planning base: main `8f18bb65d75deaaafedb8b4e6ebbd430371c1d05` at 2026-10-01 06:25:22 UTC. The candidate is standalone synthetic code; it reads no repository runtime/task data.
- Six preregistered cases × four matched episode IDs × two routes = **48 assignment rows**. The runner retains 8 primary/control rows per case and the independent auditor requires every route×episode cell.
- Construction: CPython 3.12.10 on Windows 11 AMD64; `python -m pytest -q test_method.py` → **11 passed**. The chronology, including test-harness errors and targeted red tests, is in `CONSTRUCTION_NOTES.md`.
- Candidate: `python execute_once.py` → exit **0**, exactly **1** candidate subprocess. Raw stdout SHA-256: `e8ac70f6c7cac937f1bcd8869e3a361aa7d72de0c0fb5d734cbe756a8c3dfb9c` (21,577 bytes); stderr empty.
- Independent audit: `python audit_once.py` → exit **0**, `PASS_METHOD_SCOPED`, **0 errors**, exactly **1** auditor invocation. It imported neither candidate nor candidate helpers; it reconciled the raw ledger against the frozen fixture/literal oracle and source/run receipts. Both mutations were rejected: omitted control row and altered assignment seal.
- Docker Desktop `desktop-linux` was checked read-only with `docker version --format {{.Server.Version}}`; it failed to respond within 4 seconds. No image, container, daemon mutation, or shared resource was used. This is an explicitly recorded host-only fallback, not a Docker result.

## Results

| Case | True primary contrast | Complete-case primary-only contrast | #5766-style pre/post deck | Same-cohort disposition |
|---|---:|---:|---|---|
| `clean_null` | 0.00 | 0.00 | PASS | `NO_CONTROL_SIGNAL` |
| `primary_benefit` | +0.50 | +0.50 | PASS | `NO_CONTROL_SIGNAL` |
| `route_missingness` | 0.00 | +0.75 | PASS | `ASCERTAINMENT_HOLD` |
| `foreign_join` | 0.00 | +0.75 | PASS | `JOIN_INTEGRITY_HOLD` |
| `export_drift` | 0.00 | +0.50 | HOLD | `ORACLE_DRIFT_HOLD` |
| `real_collateral` | +0.50 | +0.50 | PASS | `COLLATERAL_FAIL` |

The all-attempt frame is four episode IDs per route in each case. The naïve primary-only value is deliberately complete-case and is shown as a diagnostic comparator, not a valid #57 estimand. In the missingness case, both routes have identical underlying outcomes but three guarded failures are unobserved. In the join case, guarded outcome rows are contaminated with foreign successes; all three mismatched assignment seals are retained and detected. The scorer/export drift case changes two guarded endpoint labels while leaving raw sentinel snapshots unchanged; the reference deck and snapshot/export comparison hold. In the collateral case, a real guarded sentinel-state change is confirmed by both snapshots and export, and the disposition is safety failure, not confounding.

An additional construction test with equal missing counts on different episode IDs confirmed that per-episode missingness asymmetry still triggers a hold. Another confirms that even symmetric missing hard outcomes prevent a `NO_CONTROL_SIGNAL` disposition.

The pre/post reference-deck comparator is a small standalone realization of the complementary check-standard concept in [Issue #5766](https://github.com/Unjuno/agent-interface/issues/5766); it does not import or modify that study's code or extend its T0/T1 findings.

## Parallel Issue activity and scope correction

After candidate/audit completion, the Issue timeline was refreshed and showed comment [#5925853020](https://github.com/Unjuno/agent-interface/issues/5841#issuecomment-5925853020), posted at 06:16 UTC before this package's 06:25 UTC freeze. It is an exploratory six-case × eight-row probe, not a frozen/audited T0. Several case classes overlap this package (clean, true benefit, route loss/missingness, shared export error, real collateral); therefore this package is a **formalized scoped execution with substantial case overlap**, not independent scientific replication of that probe. Its additive audited coverage is the sealed foreign-join case, per-episode/complete-denominator checks, immutable source freeze, one-shot raw capture, and independent mutation audit.

That earlier probe also demonstrates a separate primary-only export error with an unchanged sentinel and a spurious +0.50 contrast. This package did **not** include or detect that case. Treat it as `OUT_OF_SCOPE_UNDETECTED`; do not treat this T0's `NO_CONTROL_SIGNAL` in the clean/true-benefit controls as evidence against primary-only misclassification. The parallel probe's result is not imported into this package's raw/audit or counted as one of its six cases. A later successor would need a predeclared path-sharing diagram and explicit primary-only fault class before testing incremental value over all-attempt reconciliation.

## H / T / D / C / U

**H:** A same-cohort identity/missingness/sentinel check flags planted route-correlated ascertainment cases without mislabeling clean null or true primary benefit, and distinguishes actual collateral from measurement error.

**T:** The six frozen cases, 11 construction tests, one hash-gated candidate subprocess, one separate raw-only audit, and two audit mutations are retained. The exact fixture, literal expected table, run receipt, raw bytes, stderr, and audit are provided alongside this report.

**D:** **PASS_METHOD_SCOPED.** Missingness and foreign joins that manufacture +0.75 complete-case contrasts are held; the pre/post reference deck catches the declared in-deck export drift; actual sentinel change is `COLLATERAL_FAIL`; clean null and true primary benefit have no negative-control alarm. The independent audit has zero errors and rejects both frozen corruption controls.

**C:** The pre/post deck catches only drift represented in and passed through that deck. The cohort controls work here because the sealed episode identity, complete assignment frame, and before/after sentinel snapshot are independent and available. An all-attempt accounting rule plus a strong independent final-state oracle may detect these same faults more simply. A same-cohort control adds false reassurance if it does not actually share the primary endpoint's ascertainment path.

**U:** These six deterministic synthetic cases do not estimate sensitivity, specificity, or route effects in live work. They do not establish that an ostensibly untouched GUI sentinel is causally unaffected; a route can cause real collateral. Endpoint-specific errors outside the declared shared path may escape. No historical #57 result is reclassified; no causal, safety-rate, product, or human-tempo claim follows.

## Retained files

`FREEZE.md` and `FREEZE.json` preserve the decision rule and input/source hashes; `fixture.json` and `EXPECTED.json` preserve the planted cases and independent oracle; `candidate.py` and `audit.py` are separate; `test_method.py`, `execute_once.py`, and `audit_once.py` retain tests and launch/audit gates; `results/` contains the candidate stdout/stderr, run receipt and independent audit. `SHA256SUMS.txt` binds the final package bytes.
