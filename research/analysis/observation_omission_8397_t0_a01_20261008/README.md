# Issue #8397 — T0 A01 state-conditioned observation-omission contract

This additive package retains a finite deterministic contract test for the
unverified observation-omission profile idea in
[Issue #8397](https://github.com/Unjuno/agent-interface/issues/8397).

- **Result:** `PASS_METHOD_SCOPED`; five scenarios / ten baseline-intervention
  arms reconstructed with zero mismatches.
- **Candidate / audit:** one formal invocation each, both exit 0; no retries.
- **Construction:** 7 tests passed before freeze, including five rejected
  mutation controls.
- **Evidence:** [`FREEZE.json`](FREEZE.json), [`fixture.json`](fixture.json),
  [`candidate.py`](candidate.py), [`auditor.py`](auditor.py),
  [`results/candidate_raw.json`](results/candidate_raw.json),
  [`results/audit.json`](results/audit.json), and [`SHA256SUMS.txt`](SHA256SUMS.txt).
- **Detailed outcome:** [`REPORT.md`](REPORT.md), [`RESULTS.md`](RESULTS.md), and
  [`EXECUTION.md`](EXECUTION.md).

This is native Windows standard-library execution of a synthetic method
fixture, not a container run. It does not test or satisfy the empirical H in
Issue #8397 and does not establish GUI observation value, task benefit,
safety, or a runtime scheduling policy. The next empirical rung still requires
a fresh authorized disposable GUI allocation, an exact independent effect
oracle, and cleared resource/ownership gates.
