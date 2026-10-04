# Run record

- Issue: #7709, synthetic method-only T0; frozen base `c837ad535eed085d95744ad0a9680535a5bb7143`.
- Python: CPython 3.14.5; standard library only; no network.
- Candidate: `python3 -B .../candidate.py`, one invocation, exit 0; 230,400 paired attempt rows; frozen disposition `METHOD_PASS_SCOPED`.
- Auditor v1: one invocation, exit 0; `AUDIT_FAILED`, 4/5. Failure was auditor-only floating-point recomputation (`1 - coverage` versus direct false-promotion count). Preserve `AUDIT.json` unchanged.
- Auditor v2: separately frozen and invoked once; candidate/raw/result hashes match; 8/8 checks pass; v1 failure explicitly verified and retained. Candidate and raw were not rerun or altered.
- Decision gates: session-cluster coverage ≥90% and false promotion ≤10% in all three workloads; ≥10 percentage-point coverage gain over pooled intervals in both nonstationary workloads. All passed.
- Censoring: each censored pair remains in the all-window ledger at the frozen 120 ns penalty; no rows dropped.
- Container: not required by #7709 T0. OrbStack `docker ps` inspection failed before launch on a cached containerd blob (`operation not supported`); no image pull/build/restart or container start occurred.
- Scope: synthetic interval calibration only; no actual route, model, GUI, effect, safety, or latency claim. No #59 allocation or prior-result regrade.
