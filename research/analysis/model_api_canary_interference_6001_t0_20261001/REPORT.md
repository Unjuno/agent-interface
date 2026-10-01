# Issue #6001 comment successor: canary workload interference T0

**Disposition: `PASS_METHOD_SCOPED` for the declared discrete-event fixture only.** This is a newly executed synthetic T0 for the open design refinement on [Issue #6001](https://github.com/Unjuno/agent-interface/issues/6001#issuecomment-5930382123). It is not a provider/model experiment, does not establish that any real endpoint has queue or quota coupling, and does not validate the broader hidden-model-shift proposal.

## H / T / D / C / U

- **H:** With a stable semantic model, a bracketed probe sharing a single FCFS service queue delays route B; an equal-cost sham load reproduces the workload effect, while a probe on an isolated pool does not. This can contaminate a serial A/B latency contrast. Separately, a planted in-deck semantic shift should be detected by the canary without treating queue delay as semantic change.
- **T:** Offline discrete-event simulation, no provider calls and no real model. Four policies (`no_probe`, `shared_canary`, `shared_sham`, `isolated_canary`) crossed with four scenarios (`null`, `interference_only`, `semantic_shift`, `both`), 240 deterministic replicates/cell, seed `6001001`. Each pair runs A then B; the probe is inserted after A and before B. Route service durations are `10 + U(0,0.2)` seconds. A shared canary or sham occupies the shared server for exactly 6 seconds; isolated canary consumes 6 seconds on a disjoint pool. Stationary semantic correctness is Bernoulli(0.90); planted B-block shift changes it to Bernoulli(0.55). Complete request submit/start/finish, service, eligibility and canary outcomes are retained in `raw.jsonl`.
- **D:** The preregistered fixture gate passes if shared canary and sham each add at least 5.9s mean B queue wait vs no-probe; their means agree within 0.01s; isolated and no-probe means agree within 0.01s; post-canary success is below 0.70 in both shift scenarios and at least 0.70 in every stationary null policy. An independent raw-event auditor checks row count/uniqueness, A→B order, nonnegative event durations, scenario/shift provenance and recomputes every cell summary. Result: shared canary and sham each add exactly 6.0s mean B queue wait and 6.0065s mean B-minus-A response latency; no-probe and isolated canary add 0s queue wait and 0.0065s response latency. Canary correctness is 0.5625 in shifted scenarios and 0.875 in stationary scenarios. All three auditor gate groups pass; 3,840 rows audited, zero audit errors. Four mutation/unit tests pass (duplicate row, route reordering, shift-provenance tamper, intact raw).
- **C:** The sham reproducing the effect supports shared workload occupancy—not canary semantics—as the modeled cause. This is a constructed FCFS queue with a fixed 6s probe, not a fitted or observed provider queue, quota, cache, rate limiter, or service scheduler. Probe time and route service are deliberately simplified; randomization/interleaving, concurrent external arrivals, queue priorities, cache warming, quota depletion and eligibility/censoring are absent.
- **U:** No claim about real-provider interference magnitude, prevalence, canary sensitivity, false-alarm probability, route-effect validity, model identity, GUI task quality, or product behavior. The Bernoulli shift detector is an elementary fixture threshold, not a calibrated statistical test. T1/live provider evaluation would require a separate explicit allocation, budget and prospective freeze.

## Reproduction

Run from this directory with Docker Engine and the exact image `python:3.12-slim` (`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`):

```sh
docker run --rm --pull=missing --network=none \
  -v "$PWD":/work -w /work python:3.12-slim \
  sh -lc 'python simulate.py raw.jsonl && python audit.py raw.jsonl > audit.json && python -m unittest -v test_audit.py'
```

Actual run used Docker Engine 29.4.0, OrbStack, ARM64 host; candidate, auditor and tests ran as separate processes inside fresh `python:3.12-slim` container invocations with networking disabled. The first construction audit invocation found an expectation bug (`expected 3200 unique rows, got 3840`); no PASS was claimed from that invocation. Only the audit denominator was corrected to the frozen 4×4×240 design, then the complete raw file was re-audited. A second full candidate run was byte-identical (`raw.jsonl` and `raw-repeat.jsonl`, SHA-256 `b2e97431f2e11f21fbbb8a827556405e6f489648890b9e63e73423280a9c3356`).

The local reconstruction of the generated analysis-index gate against this PR's Git tree found ten pre-existing retained result directories on preparation `main` that were absent from its generated list. Their index links are added alongside this result so the block matches the retained REPORT/FORMAL_FAILURE directory set; no existing artifact or scientific status was changed.

## Frozen identities

- Candidate source SHA-256: `f00a75328090412d9557f81c1e5fe34696cbf66a4e8ba910faa44862320f7bec`
- Independent auditor SHA-256: `db79257a54381613d00383fd9b4af0896b0c279d39787e94e134291c9759b800`
- Mutation tests SHA-256: `9ad5252c0e05412ad30194bb2b85206360da0408b401056d0147595fa9242846`
- Raw rows SHA-256: `b2e97431f2e11f21fbbb8a827556405e6f489648890b9e63e73423280a9c3356`
- Audit JSON SHA-256: `5de8c977b54f378e6d1bebc077921b1274de7699c4459043ba4c212d4f23cbcd`
- Preparation main: `6cd70ad4bfad74e11658057bf024918bffb24add`.

This additive successor does not change either prior allocation STOP on #6001 and does not authorize another formal/provider allocation.
