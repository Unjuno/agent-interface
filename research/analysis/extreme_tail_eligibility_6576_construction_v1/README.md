# Issue #6576 — eligibility-gate construction experiment (host-only)

This is a bounded construction/boundary experiment, not the proposed containerized T0 and not release-delay evidence. It asks whether a typed eligibility gate can distinguish a fully observed reference from explicitly represented missing-mode, insufficient per-mode tail support, drift, dependence, and censoring conditions. It does not generate timing distributions or evaluate EVT/TailID. No observed-release samples are used.

## H / T / D / C / U

- **H:** An explicit evidence-eligibility gate can allow a fully observed stationary reference while refusing tail interpretation when declared mode coverage, temporal stability, dependence, or endpoint observation is violated.
- **T:** Deterministic finite boundary cases feed a pure gate. Compare decisions to an independently stated truth table; include explicit metadata mismatch, mode sample count below the frozen 40-row minimum, drift, dependence, censoring, and missing endpoint.
- **D:** Construction experiment only. PASS means the implementation obeys this finite contract; the value 40 is a construction fixture, not a validated minimum sample size. This does not validate statistical power, a named EVT estimator, TailID, real release timing, or a safety tail bound.
- **C:** macOS host Python; no Docker/OrbStack, WSLc, GPU, model, GUI, OS input, or live release instrumentation. Formal container T0 remains unrun pending an exclusive assigned lane.
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

### Attempt record

- Attempt 01: direct script invocation stopped before candidate computation (`ModuleNotFoundError: No module named 'research'`); candidate rows=0, auditor=0. No scientific disposition.
- Boundary A01: six cases, raw-only audit PASS 6/6 (five rejection controls); construction tests 8/8. Preserved at `candidate_output_boundary_a01.json`.
- Boundary A02: after adding mode-specific minimum tail support, seven cases, raw-only audit PASS 7/7 (six rejection controls); construction tests 9/9. Preserved at `candidate_output_boundary_a02.json`.
- TailID-port construction attempt 01: focused suite 12/13; candidate-count calculation exposed floating-point truncation (19 instead of the frozen 20) before any formal study. Corrected attempt 02 passed 13/13, but only self-tests; numerical equivalence with the pinned TailID/ismev R implementation remains unverified.
- Both boundary runs used host CPython 3.14.5; neither used a container and neither is the formal T0 allocation.
- Candidate direct-script invocation was reproduced as STOP (`ModuleNotFoundError: No module named 'research'`, zero candidate/audit rows); module invocation was then run separately and raw-only audit passed 7/7. The preserved boundary A02 output hash is `90901d18023c723c47450f90e85477b26c72a56c8b5dcfdb3265c5604fdcd1ec`.
- Runtime-shift construction tests: first run 3/4 because positive infinity was accepted; the finite-input guard was fixed, and the combined construction suite passed 17/17. The exact synthetic case confirms that a detected shift can still be inadequate when a safety-deadline miss occurs before alarm. This is not a detector false-alarm/delay estimate.

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
