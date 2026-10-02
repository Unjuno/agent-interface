# Issue #6576 — eligibility-gate construction and tail-comparator experiments

The initial bounded construction/boundary experiment is distinct from the later CRAN/R comparator studies and from the proposed formal containerized T0. It asks whether a typed eligibility gate can distinguish a fully observed reference from explicitly represented missing-mode, insufficient per-mode tail support, drift, dependence, and censoring conditions. No observed-release samples are used.

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
The Python TailID port has now been compared against the pinned CRAN/R code in
three additive one-shot successors. A03 stopped before R evaluation due to a
candidate harness input-shape error; A04 candidates completed but its auditor
crashed and its supplemental per-step trace was non-cumulative; A05 completed
the raw-only audit and failed numerical MLE/CI parity on one of six fresh
synthetic fixtures while candidate/sensitive index and threshold checks
passed. The Python port is not established as numerically equivalent to
CRAN/ismev. Full results and immutable raw outputs are linked below.

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

- The preregistration lane start gate was then clarified to allow either an explicitly released/assigned shared Engine or an explicitly assigned dedicated isolated OrbStack daemon. Its current SHA-256 is `da3488dc8dfa9fbec514781a2bd405e8fd9ebbf3648afb694c8eecbc44463f96`; this supersedes the earlier `T0_PREREGISTRATION.md` hash above. Other prepared-source hashes above are unchanged.

- Construction censor-cap probe A01: one distinct host-only case (seed 65761101, 2,000 train/2,000 holdout) candidate exit 0 and independent auditor exit 0, `PASS_METHOD_SCOPED PASS_RAW_ONLY`, retries 0. Train/holdout censor counts 21/20; gate `NOT_ESTIMABLE_CENSORED_ENDPOINT`; all three holdout score records `NOT_ESTIMABLE_CENSORED_HOLDOUT`. Raw and run provenance are retained under `construction_censor_cap_probe_a01/`. This is code-path construction evidence only, not formal T0 or calibration/safety evidence.

- Construction censor-cap probe A01: one distinct host-only case (seed 65761101, 2,000 train/2,000 holdout) candidate exit 0 and independent auditor exit 0, `PASS_METHOD_SCOPED PASS_RAW_ONLY`, retries 0. Train/holdout censor counts 21/20; gate `NOT_ESTIMABLE_CENSORED_ENDPOINT`; all three holdout score records `NOT_ESTIMABLE_CENSORED_HOLDOUT`. Raw and run provenance are retained under `construction_censor_cap_probe_a01/`. This is code-path construction evidence only, not formal T0 or calibration/safety evidence.

### CRAN/R parity successors (executed; separate from formal T0)

- [A03](orbstack_cran_parity_a03_20261002/RUN_RECORD.md): R candidate harness
  stopped before sample evaluation (`R=1`, Python arm `0`); no parity result,
  no retry.
- [A04](orbstack_cran_parity_a04_20261002/RUN_RECORD.md): both candidate arms
  ran, but its one-shot auditor crashed formatting a mismatch; the post-hoc raw
  review is explicitly not a formal audit.
- [A05](orbstack_cran_parity_a05_20261002/RUN_RECORD.md): six fresh fixtures;
  candidate order, sensitive-index sets, thresholds and R convergence passed,
  but one base MLE/CI exceeded frozen numeric tolerances. Overall
  `FAIL_PARITY_NUMERICAL_MLE`.
- [A06](orbstack_optimizer_sensitivity_a06_20261002/RUN_RECORD.md): both
  fresh-seed candidate arms stopped before producing fits because container UID
  1000 could not write to VM-host UID 501 output mounts; auditor correctly did
  not run. This is infrastructure STOP only.
- [A07](orbstack_optimizer_sensitivity_a07_20261002/RUN_RECORD.md): both
  fresh-seed candidates produced raw fits, but its one-shot auditor treated
  expected failed starts as invalid receipts. Retained as
  `STOP_AUDITOR_CLASSIFICATION_MISMATCH`; no audit rerun.
- [A08](orbstack_optimizer_sensitivity_a08_20261002/RUN_RECORD.md): fresh
  six-case candidate and failed-start-aware independent audit passed. Four of
  six fixtures exceeded the preregistered converged-R-fit sensitivity gate;
  default R/Python numerical parity passed six of six. A05's specific
  discrepancy cause remains unproven.

These are method-comparator studies on dedicated isolated OrbStack Docker
containers, not allocation #6576 T0. Their failures and scope boundaries remain
separate; all raw inputs, outputs, source, image identities and hashes are
retained. None establishes a real release-delay tail, physical key-up, safety,
or worst-case guarantee.

### Execution status and local CI / provenance checks

The earlier host-only boundary package and censor-cap probe remain preserved.
Pilot A01's OrbStack-machine process stopped before raw persistence due to a
root-owned output directory; that allocation was not retried. Its successor,
[OrbStack Docker pilot A02](orbstack_pilot_a02_20261002/RUN_RECORD.md), ran one
new stationary synthetic case in a dedicated nested Docker Engine. Candidate
and raw-only auditor each ran once, exited 0, and the audit returned
`PASS_METHOD_SCOPED PASS_RAW_ONLY cases=1 train=4000 holdout=4000`. This is a
single-case pilot only, not the formal six-case T0 or an input-release result.

After refreshing through current main `a81614d975631b1c2d0ad78fe98e4e96ba20b93a`,
the focused construction suite passes 24/24; `py_compile` and `git diff
--check` pass. The A02 raw output and all source/input/output hashes are checked
in `orbstack_pilot_a02_20261002/SHA256SUMS`.
Repository-wide `python3 research/analysis/check_index.py`:
FAIL, reporting broad pre-existing stale generated entries across unrelated
analysis directories. Its suggested `--write` was deliberately not run because
it would modify unrelated shared research history. The formal six-case
candidate/auditor remain uninvoked (0/0), and the #5085 formal allocation still
has no exact assignment/release recorded. A02 and the parity experiments used
dedicated OrbStack Docker Engines; none used the shared
`unjuno-native-ci-6092` container.

The formal T0 remains pending. At its assigned start, recheck and freeze the
exact current main and all input/source/image hashes before candidate
invocation.
