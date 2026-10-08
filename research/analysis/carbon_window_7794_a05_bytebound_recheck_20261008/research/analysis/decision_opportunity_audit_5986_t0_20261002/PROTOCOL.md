# Issue #5986 — immutable T0 raw independent audit

## H / T / D / C / U

**H.** A separately implemented, raw-only auditor in a pinned isolated container will reproduce all six retained classifications and timing/cost fields from the original fixture and candidate JSON, while rejecting materially corrupted rows. This is an audit replication, not another candidate allocation.

**T.** Freeze the predecessor PR #6131 commit, FREEZE, fixture, candidate JSON and its hashes. Before the formal audit, run construction tests against the frozen bytes. Then invoke only the new independent auditor once in OrbStack Docker; mount source read-only, disable network, use a separate writable result mount and resource limits. The auditor must not import predecessor candidate.py or audit.py. No candidate, GUI, model, app, or action is run.

**D.** `PASS_AUDIT_REPRODUCED_SCOPED` iff the independent reconstruction matches every raw field across all six cases, the authored classification distinctions and zero empirical-value promotion hold, all six mutations reject, and process exit is 0. Any discrepancy is retained as FAIL/STOP; no repair/retry of this allocation.

**C.** Original frozen candidate JSON SHA-256 is `c3023018f657e33c4d6a9bf70a956bfa030b04fdde32671a096e1d0a02a51a2f`; fixture SHA-256 is `a2dac053fd3c2b5aea63b2d48bcb11cdce3a7faa1542b8a7e8c153d256403a53`. The original candidate and audit are not rerun or altered. All cases, clocks and effects remain synthetic.

**U.** This audit establishes neither whether earlier feedback benefits a real bounded agent nor real safety, GUI task effects, latency, cost, human tempo, or transfer. It does not resolve the pending/censored route-learning hypothesis in #6129.

## Fixed execution

Source main: `d6229435f9d651b5309a01dca30c2edd7de2f54a`. Predecessor #6131 head: `357989191b85cd4ed4ecacb313170b6294e56a62`. Formal allocation `DECISION-OPPORTUNITY-5986-AUDIT-20261002-01`; candidate invocations 0, independent auditor 1, retries 0. Pinned image and container flags are in FREEZE.json.

Exact container command:

```sh
docker run --rm --network none --read-only --cpus 0.5 --memory 256m --pids-limit 32 --cap-drop ALL --security-opt no-new-privileges \
  -v "$PWD:/study:ro" -v "$PWD/out:/out:rw" \
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /study/independent_audit.py /study/frozen/fixture.json /study/frozen/candidate.json /out/audit.json
```
