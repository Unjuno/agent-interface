# Issue #6576 — eligibility-gate construction experiment (host-only)

This is a bounded construction/boundary experiment, not the proposed containerized T0 and not release-delay evidence. It asks whether a typed eligibility gate can distinguish a fully observed reference from explicitly represented missing-mode, insufficient per-mode tail support, drift, dependence, and censoring conditions. It does not generate timing distributions or evaluate EVT/TailID. No observed-release samples are used.

## H / T / D / C / U

- **H:** An explicit evidence-eligibility gate can allow a fully observed stationary reference while refusing tail interpretation when declared mode coverage, temporal stability, dependence, or endpoint observation is violated.
- **T:** Deterministic finite boundary cases feed a pure gate. Compare decisions to an independently stated truth table; include explicit metadata mismatch, mode sample count below the frozen 40-row minimum, drift, dependence, censoring, and missing endpoint.
- **D:** Construction experiment only. PASS means the implementation obeys this finite contract; the value 40 is a construction fixture, not a validated minimum sample size. This does not validate statistical power, a named EVT estimator, TailID, real release timing, or a safety tail bound.
- **C:** The bounded construction checks used macOS host Python; no formal OrbStack T0, GPU, model, GUI, OS input, or live release instrumentation. Formal T0 remains unrun pending an exclusive assigned lane.
- **U:** Distributional validity, rare-event calibration, unseen modes, real-world stationarity, detector operating characteristics, and protection before a real safety deadline remain untested. The added runtime-shift probe below is a deterministic contract check only.

## Construction experiment

`test_gate.py` exercises the finite boundary contract. `candidate.py` processes `cases.json`; `audit.py` independently checks only the input hash and exact case-to-decision mapping without importing candidate logic. Run with:

```sh
python3 -m unittest -v research.analysis.extreme_tail_eligibility_6576_construction_v1.test_gate
python3 -m unittest -v research.analysis.extreme_tail_eligibility_6576_construction_v1.test_runtime_shift
python3 -m unittest -v research.analysis.extreme_tail_eligibility_6576_construction_v1.test_tailid_equivalent
python3 -m research.analysis.extreme_tail_eligibility_6576_construction_v1.candidate \
  research/analysis/extreme_tail_eligibility_6576_construction_v1/cases.json /tmp/6576-candidate.json
python3 research/analysis/extreme_tail_eligibility_6576_construction_v1/audit.py \
  research/analysis/extreme_tail_eligibility_6576_construction_v1/cases.json /tmp/6576-candidate.json
```

This result must not be represented as #6576 T0. A separate, prospectively frozen container allocation with generated timing data, naive empirical/max and EVT/TailID comparators, held-out coverage, raw-only independent audit, and exact image/source identities is still required.

### Formal T0 runner preparation — not invoked

`T0_PREREGISTRATION.md`, `t0_cases.json`, `t0_candidate.py`, and
`t0_audit.py` now define the one-shot T0 package. The candidate generates six
fixed-seed synthetic train/holdout pairs (4,000 rows each), reports pooled
empirical p95/max and naive GPD p99, runs the source-backed TailID equivalent,
and only emits a mode-stratified gated EVT p99 when the gate allows it. The
auditor imports none of the candidate/gate/TailID modules; it independently
reconstructs every generated row and recomputes typed decisions, empirical
statistics, held-out exceedance counts, coverage flags, and exact binomial
intervals. The frozen minimum of 40 is an observed exceedance count; it does
not itself establish independence, which is handled by a separate diagnostic.

This is still preparation, not formal evidence: the frozen six-case candidate
and auditor have not been invoked; no formal timing rows, output hash, or
method disposition exists. Formal candidate once, then auditor once only if
candidate exits 0, require the exact exclusive OrbStack grant under #5085.
The TailID port remains without numeric comparison to CRAN/R.

### Attempt record

- Attempt 01: direct script invocation stopped before candidate computation (`ModuleNotFoundError: No module named 'research'`); candidate rows=0, auditor=0. No scientific disposition.
- Boundary A01: six cases, raw-only audit PASS 6/6 (five rejection controls); construction tests 8/8. Preserved at `candidate_output_boundary_a01.json`.
- Boundary A02: after adding mode-specific minimum tail support, seven cases, raw-only audit PASS 7/7 (six rejection controls); construction tests 9/9. Preserved at `candidate_output_boundary_a02.json`.
- TailID-port construction attempt 01: focused suite 12/13; candidate-count calculation exposed floating-point truncation (19 instead of the frozen 20) before any formal study. Corrected attempt 02 passed 13/13, but only self-tests; numerical equivalence with the pinned TailID/ismev R implementation remains unverified.
- Both boundary runs used host CPython 3.14.5; neither used a container and neither is the formal T0 allocation.
- Candidate direct-script invocation was reproduced as STOP (`ModuleNotFoundError: No module named 'research'`, zero candidate/audit rows); module invocation was then run separately and raw-only audit passed 7/7. The preserved boundary A02 output hash is `90901d18023c723c47450f90e85477b26c72a56c8b5dcfdb3265c5604fdcd1ec`.
- Runtime-shift construction tests: first run 3/4 because positive infinity was accepted; the finite-input guard was fixed. The exact synthetic case confirms that a detected shift can still be inadequate when a safety-deadline miss occurs before alarm. This is not a detector false-alarm/delay estimate.
- T0 construction attempt 01: 21 focused tests exposed an exact-binomial lower-bound bisection error and a censored case being classified first as nonstationary. Both were corrected; focused suite now passes 21/21. This test run only generated 200-row helper fixtures plus existing construction tests; it did not call the formal six-case candidate on its frozen inputs.
- T0 construction attempt 02: code review found that scoring only uncensored holdout rows would estimate a selected-subpopulation exceedance rate under informative censoring. The candidate now returns `NOT_ESTIMABLE_CENSORED_HOLDOUT` for every comparator if any holdout endpoint is censored, and the independent auditor enforces that refusal. A focused unit test was added; this is a pre-formal correction, not a formal run.
- T0 construction attempt 03: independent profile-likelihood recomputation was added to the raw auditor for naive, gated, and TailID GPD outputs; the oracle also independently reconstructs the TailID candidate/sensitive set. A toy candidate+auditor integration fixture passed, and a deliberately corrupted naive p99 was rejected with `FAIL_NAIVE_EVT_P99`. Tests across six separate 400-row construction scenarios matched candidate GPD parameters and TailID selection. This exposed a pre-formal candidate exception: complete-case training on the censoring scenario could make TailID's stipulated candidate count non-integral. Comparators now use all reported endpoint values (including the censor cap, explicitly as a deliberately naive baseline); the gate still refuses censored training and holdout coverage stays `NOT_ESTIMABLE_CENSORED_HOLDOUT`. Combined focused suite 24/24 PASS; `py_compile` and `git diff --check` PASS. No frozen formal cases were invoked.
- Current prepared-source SHA-256 after attempt 03: `T0_PREREGISTRATION.md` `b54ac40c9733f689a2464b2fc386a5bda297d1c4c284b9a7f4f6aee8e3b5f09f`; `t0_cases.json` `05a2f44dd672dae2548bdb0e6f7e15680948dae7f3cbcac3cdc257eef4737`; `t0_candidate.py` `d474ed30c29866d3cccf0e8e593bea5135a227878a32636714f40062c54d4107`; `t0_audit.py` `4e37d74b3568e9b1ee88063263a8f2cb186f47eded9d357fc13e326f6e76483a`; `test_t0_construction.py` `49fa98fc786460a45bf26bed677752b8034f99a789c64e186a1c212802e5c57d`; `test_gate.py` `6783e35e1aa54a5e21eacb7271ab697d73faa8d494abea980f2fdcf45a5eb576`; `gate.py` `006380d64f8c5859e950efb19da8623a89a7b722489619ef2c25411e66b20ff4`; `tailid_equivalent.py` `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`.
- Focused preparation suite after censoring-score review: 22/22 PASS; `py_compile` and `git diff --check`: PASS. These remain construction checks only; the six frozen formal cases were not invoked. Current SHA-256: `T0_PREREGISTRATION.md` `ba178672b6f38ec9c7171e736c2a1d36af288d28f66a18fa71d2dd47bb8bb733`; `t0_cases.json` `05a2f44dd672dae2548bdb0e6f7e15680948dae6bf7e3cbcac3cdc257eef4737`; `t0_candidate.py` `1f7eae526359b39c86e162914646ab1d381b7fa94fe210461326e4231ed74821`; `t0_audit.py` `ba49ff961eab3d1265b550d0d43b764390ab4541b5b2f0e94d415cc8e2fe215a`; `test_t0_construction.py` `e03a6898cd21eea8823e8417afea22e9d9db5cec5581aa4cee60b6c28800a3c1`; `test_gate.py` `6783e35e1aa54a5e21eacb7271ab697d73faa8d494abea980f2fdcf45a5eb576`; `gate.py` `006380d64f8c5859e950efb19da8623a89a7b722489619ef2c25411e66b20ff4`; `tailid_equivalent.py` `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`.

### One-shot comparator runner preparation (not executed)

The outstanding #6576 T0 comparator is the original R implementation, not the
provisional Python port. A future exclusively assigned container run should
mount read-only copies of TailID 1.0.0 at commit
`f99b10ff27f37ac62ba1d44ce79b4fc886f72997` and ismev at commit
`25223b17285d45bf3911efd79ac75f363e7ae495`, plus a write-only output mount;
disable network and pull, and freeze package/library hashes before invoking
the candidate. The source-backed Python port must be compared on identical
fixtures for threshold, candidate count, GPD fit, selected sensitive tail and
typed refusal. Candidate, then raw-only audit, each run at most once. This
paragraph is a protocol note only: no R image was pulled, no container was
started, and no comparator parity result exists.

### Current local CI / provenance checks

On 2026-10-02, the preparation branch was successively reconciled with main
through `7b5afc3d718682b7b6efb2e6037acbd3f199f8b4`,
`6942e950281832d01db6468ae47affef6513e3ba`, and later PR-head merges. The
latest base must be refreshed again at formal start.
Focused construction suite: 17/17 PASS; `py_compile`: PASS; `git diff
--check`: PASS. Candidate module plus independent raw-only audit: PASS 7/7.
Repository-wide `python3 research/analysis/check_index.py`:
FAIL, reporting broad pre-existing stale generated entries across unrelated
analysis directories. Its suggested `--write` was deliberately not run because
it would modify unrelated shared research history. No new result-index entry
was written. The formal request in #5085 remains unassigned; the active
`unjuno-native-ci-6092` container is still running, so no Docker experiment was
started.

This rebase is preparation-only, not an execution freeze. At any formally
assigned start, recheck and freeze the exact current main and all input/source/
image hashes before candidate invocation.
