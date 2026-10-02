# Construction censor-cap probe A01 — run record

Disposition: `PASS_CONSTRUCTION_ONLY`; not formal T0 and not scientific
calibration evidence.

- Frozen branch HEAD: `126728e677b00f296403e6ff564c574105a37902`; main at freeze:
  `afea9a530cafd7af529df4c9e59f36b816bca24f`.
- Environment: macOS host, CPython 3.14.5, CPU only. No container, GPU, model,
  GUI, OS input or external data. OrbStack formal allocation was not assigned.
- Candidate invocation: 1, exit 0. Auditor invocation: 1, exit 0. Retries: 0.
- Candidate command:
  `python3 -B -m research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_candidate research/analysis/extreme_tail_eligibility_6576_construction_v1/construction_censor_cap_probe_a01/cases.json research/analysis/extreme_tail_eligibility_6576_construction_v1/construction_censor_cap_probe_a01/candidate.raw.json`
- Auditor command:
  `python3 -B -m research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_audit research/analysis/extreme_tail_eligibility_6576_construction_v1/construction_censor_cap_probe_a01/cases.json research/analysis/extreme_tail_eligibility_6576_construction_v1/construction_censor_cap_probe_a01/candidate.raw.json`.
- Raw-only auditor output is retained in `audit.txt`: `PASS_METHOD_SCOPED
  PASS_RAW_ONLY cases=1 train=2000 holdout=2000`.

## Observed outputs

- Train: 21/2,000 censored; holdout: 20/2,000 censored.
- Gate: `NOT_ESTIMABLE_CENSORED_ENDPOINT`. The recorded block-median ratio
  was 1.75295 (also beyond the 1.5 construction threshold), but the gate's
  frozen structural-censor precedence correctly retained the censor reason.
- Every holdout comparator (`naive_evt`, `eligible_gated_evt`,
  `tailid_adjusted_evt`) had null exceedance count, Clopper-Pearson interval,
  and coverage flag, with reason `NOT_ESTIMABLE_CENSORED_HOLDOUT`.
- The deliberately naive train-only comparator values were empirical p95
  2.90252, max 5.88966, naive EVT p99 3.98969, and TailID-adjusted EVT p99
  3.77345. They have no scored holdout calibration in this censored case and
  must not be interpreted as population quantiles or safety bounds.

## Provenance

- `cases.json`: `9d6e447750799a8b8b82ee70c6268d1122e88cdf12f6aeb4c7bc2f42b9727f72`
- `PREREGISTRATION.md`: `9c8f4ed65f53495df9e46860cd02915c8aec9363ed9cd90874cb1753906a43ae`
- `FREEZE.json`: `cb18ee30391b92346a6b49c4b9cad329a410608d78b65f1cbe86aa4d3803176c`
- `candidate.raw.json`: `fd3a45af979903f6af89c8d658cc21f448876d2f1d46aa9482d458daa3f64089`
- `t0_candidate.py`: `d474ed30c29866d3cccf0e8e593bea5135a227878a32636714f40062c54d4107`
- `t0_audit.py`: `4e37d74b3568e9b1ee88063263a8f2cb186f47eded9d357fc13e326f6e76483a`

The separate six-case formal T0 remains uninvoked (candidate/auditor 0/0).
This host construction result does not replace its assigned OrbStack run.
