# #8594 A01 — reverse-stress minimum-bundle synthesis (T0)

**Outcome: PASS_METHOD_SCOPED (finite authored fixture only).** The official A01 candidate and independent raw-only auditor were each invoked once after the exact source hashes and decision gate were frozen on [Issue #8594](https://github.com/Unjuno/agent-interface/issues/8594#issuecomment-6060163729). Construction invocations were separate and are not pooled. This evidence does not claim deployed reliability, real GUI task success, any model result, or resolution of [real-time-control #59](https://github.com/Unjuno/agent-interface/issues/59).

## Frozen H/T/D/C/U

- **H:** A constraint-aware reverse search finds every Pareto-minimal legal failure bundle for the preregistered adverse endpoint, with a >=20% sparse-case reduction in distinct endpoint-oracle calls against exhaustive enumeration.
- **T:** 12 binary disturbances (4096 raw combinations); two parent/child implications; fixed reset, release/receipt event ordering, one 100 ms synthetic deadline; a sparse planted 1-/2-/3-way control and dense >=5 disturbance control. Compare independent exhaustive oracle, fixed weight<=2 plus maximal portfolio, seeded equal-call random, and equal-call Gray-order. Rebuild exact event traces and each legal single-removal neighbor. Run raw-only endpoint/event-order/legality/boundary corruption checks. No external state.
- **D:** PASS_METHOD_SCOPED only with exact minimal-set match, valid/replayable event traces, all legal safe neighbors, strict UNKNOWN and ILLEGAL handling, all four audit mutations rejected, and >=20% sparse call reduction. Else retain FAIL/HOLD.
- **C:** The advantage may disappear on other interaction densities or causal grammars; fixed portfolios may be easier when only decision-relevant failures matter.
- **U:** Synthetic authored transition model and monotone Boolean disturbance ladder. Causal constraints and prior are not empirically estimated; no inference to real failure probability, external model, actual deadlines or task effects. The wall-time values are single-run process observations, not throughput benchmarks.

## Official raw results (exact first outcome)

| Case | Legal scenarios | Adverse scenarios | Minimal failure bundles | Exhaustive oracle calls | Reverse distinct oracle calls | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sparse | 2,304 | 1,884 | 5 | 2,304 | 227 | 90.15% |
| Dense negative control | 2,304 | 2,056 | 111 | 2,304 | 383 | 83.38% |

Sparse minimum flags (see `spec.json` for exact indexed meanings): `1` release_slow; `6` queue_backlog+cancel_late; `56` observation_stale+focus_mutation+verification_deferred; `192` receipt_late+audit_gap; `1792` lease_renewed+renewal_overlap+scheduler_spike.

Both cases matched independent exhaustive minimal sets. The independently reconstructed query schedule and all trace/neighbor receipts matched the candidate's raw output. Dense retained 111 minima rather than 5; its measured reduction on this particular fixture must **not** be extrapolated to dense systems generally.

**Baselines (coverage of exact minimal bundles, not general failure detection):**

| Case | Fixed <=2 + maximal | Seeded random, equal calls | Gray order, equal calls | Reverse |
| --- | ---: | ---: | ---: | ---: |
| Sparse (5) | 3 | 0 | 4 | 5 |
| Dense (111) | 3 | 15 | 10 | 111 |

Four independently applied mutations to **copies** of the official raw were rejected: endpoint identity, event permutation, an illegal bundle, and a receipt boundary-value change. Unknown extra transition stays UNKNOWN, not a safe fallback. Both official processes exit code 0; stderr is empty.

## Provenance / exact reproduction

- Allocation: `REVERSE-STRESS-8594-T0-A01-20261008`.
- Main intake SHA: `f99ac0d3ad084c244cc7558d2219ac87247ded0c`; dedicated additive branch, no modification of historical outcomes.
- Tool-container: Debian GNU/Linux 13 (trixie), Linux x86_64, Python 3.13.5, AMD EPYC 9V74; no Docker/Podman/WSLc executable; base image digest is not exposed. This is **not** a qualified WSLc or OrbStack result, and no GPU/GUI/model/resource lease was claimed.
- Predeclared source SHA-256: `spec.json aed41e0cff8eab71f2594536c0463e076b5c4d2fb3f1f59135b8b608444d1f24`, `candidate.py 58082adb2029231578066cc1ed90360388baa58c2a95436e9d9b4a7e7a671a3d`, `audit.py 201f471429989652f3d268a7de43f5eebb59447967701697978998cb17af3748`.
- Raw candidate SHA-256: `2fc8d77357540782230521e9053d4b6c1f05064b71905c71a4895ac6a74c534c`.
- Raw audit SHA-256: `8065d0d25e1fd9002ab786698006fd756a928f090744c7a935505fae45389b70`.
- Reproducible evidence archive: `bundle-a01.tar.gz` SHA-256 `ef43163ef12c2a596e38e051330aa14ac42244d802cc614343adbd58a76a4bea`, containing exact scripts/spec/raw/stdout/stderr/exit codes/hashes. Binary Git blob must match before treating publication as complete.

Reproduce from extracted archive:

```bash
tar -xzf bundle-a01.tar.gz
python3 candidate.py --spec spec.json --out new_candidate.json
python3 audit.py --spec spec.json --candidate-source candidate.py --input new_candidate.json --out new_audit.json
```

Different run timings and candidate output hashes are expected because the raw includes `elapsed_ns`; verify semantic summaries and per-run audit rather than equating the new timed bytes with retained official bytes. Python standard library only, no hardware backend ABI, floating-point probability, GPU, zero-point calibration or external calls. Time values use integer milliseconds in the synthetic model; per-process elapsed times use nanoseconds.

## Error check / decision boundary

Exact-set match: PASS. Legal/replayable traces: PASS. Immediate legal neighbors: PASS. UNKNOWN preserved: PASS. Mutations 4/4 detected: PASS. Sparse improvement threshold >=20%: PASS. Real-world interface correctness/latency: **UNTESTED**. User-facing release: **NOT AUTHORIZED**.

**Next:** A separate #59-relevant test could map one observed live cancellation/release trace into this grammar and assess coverage on a genuinely independent event source. It needs a new freeze, owner/resource check, and independent acceptance contract; never interpret this synthetic PASS as a runtime guard or authorization to run a live controller.
