# Conditional end-to-end deadline certificate — T0 method result

Allocation `ROUTE-DEADLINE-6059-T0-20261001-01`; Issue [#6059](https://github.com/Unjuno/agent-interface/issues/6059).

**Disposition: `PASS_METHOD_SCOPED`.** Nine frozen scenarios passed an independent exhaustive finite-trace audit with zero errors. This is synthetic method evidence only: no Agent Interface runtime, GUI, model, user task, latency guarantee, safety claim, or production feasibility was tested.

## H / T / D / C / U

- **H:** Conditional path bounds can certify some bounded typed-terminal routes. An upper bound larger than the deadline is inconclusive; impossibility requires an independent, sound strict lower bound. Unsupported, unbounded, or assumption-invalid routes remain UNKNOWN.
- **T:** Candidate and independent exact simulator ran once each against nine frozen scenarios. The two-queue FIFO burst case enumerates 81 service assignments; target B completes at `A1 + max(B1, A2) + B2`. All nine scenario-specific trace sets were exhaustively checked (120 traces total). The candidate and auditor are separate modules; `audit.py` does not import `candidate.py`.
- **D:** `PASS_METHOD_SCOPED`: labels agree on all nine cases; both MET cases are on time on all 16 enumerated traces; the IMPOSSIBLE case misses on all four traces and carries an independent lower bound of 6 > deadline 5; the burst case spans 3–9 against deadline 8 and is UNKNOWN; absent/empirical guarantees, an unbounded stage, invalid assumptions, and shared-resource interference remain UNKNOWN. Audit errors: 0.
- **C:** This tiny queue model may omit real route branching, retries, hidden contention, scheduler behavior, clock effects, and semantic endpoint costs. The sufficient bound can be pessimistic.
- **U:** No real service envelope has been established. A timely typed terminal disposition does not imply useful task completion. T1/T2 applicability remains untested.

## Formal results

| Scenario | Certificate | Exact completion range | Traces |
|---|---|---:|---:|
| bounded serial | `CERTIFIED_DEADLINE_MET` | 2–4 / deadline 5 | 4 |
| local checks pass, FIFO burst path | `UNKNOWN_UPPER_BOUND_EXCEEDS_DEADLINE` | 3–9 / deadline 8 | 81 |
| independent lower bound proves miss | `CERTIFIED_DEADLINE_IMPOSSIBLE` | 6–8 / deadline 5 | 4 |
| shared resource interference | `UNKNOWN_SHARED_RESOURCE_CONTENTION` | 7–9 / deadline 4 | 4 |
| finite timeout + bounded cancellation | `CERTIFIED_DEADLINE_MET` | 2–6 / deadline 6 | 12 |
| unbounded stage, no enforced terminal bound | `UNKNOWN_UNBOUNDED_STAGE` | 1–20 / deadline 10 | 3 |
| empirical-only service claim | `UNKNOWN_NO_SERVICE_GUARANTEE` | 1–2 / deadline 10 | 2 |
| invalid assumption | `UNKNOWN_ASSUMPTION_VIOLATED` | 1–2 / deadline 10 | 2 |
| empirical lower bound | `UNKNOWN_NO_SERVICE_GUARANTEE` | 1–8 / deadline 5 | 8 |

The construction phase first exposed an unsound naive stage-sum on the burst case (it would label a path MET at 6 ≤ 8 even though the exact worst completion is 9). That pre-freeze failure was preserved in `FREEZE.json`; the candidate was corrected before formal freeze and the construction suite then passed 4/4. No formal output was used to change the source.

Pre-PR packaging review also caught an incorrect repository-path mapping in the first evidence-staging commit: it overlaid unrelated root-level report/output paths on the branch. Main was never changed and no PR was opened. The final evidence tree is being rebuilt from the exact source-freeze tree, restoring the original root contents and placing every result only beneath this allocation's additive directory; the intermediate branch commit remains visible in history as a packaging failure, not scientific evidence.

## Provenance and reproduction

- Frozen base and source commit parent: `9371fda8617bdf49e7fbeebb04fa64a633712aaa`.
- Source freeze commit: `a505e29559aaba445f139853f29dc838d621158f`, with the exact base as its only parent.
- At publication preflight main had advanced to `152c1b499c16af0bd5a385eb0cd829cdcadaae7c`; comparison found eight changed paths, all under the unrelated `research/integration/navigation_readiness_2858_r0_k7p3_v1/` allocation. No overlap with this additive study path or `research/analysis/README.md`.
- Python 3.12.10, Windows NT 10.0.26200.0; standard library only.
- Candidate invocation: exit 0, 129.140 ms, `candidate complete: 9 certificates`.
- Auditor invocation: exit 0, 113.046 ms, `audit PASS_METHOD_SCOPED: 9 cases; 0 errors`.
- Candidate output SHA-256: `449F8A364F1144D075AE61D6DF667D5DB1182F15A4D67BD9D03313F0FC67C375`.
- Auditor report SHA-256: `58A1C13E7D428BC354B5E4020B9C6A4C644B78AF4FB1D460D41ABAD04DDB0355`.
- Frozen input SHA-256: `EB4230E752669E9F3B680B5E684F25F481B5832D3629D4F790BE98445F07B567`.
- Candidate stdout SHA-256: `D356EF35C404DE89A2178D562D96553CDD6CB112560A605D8D1CF10AE7FCE13B`; auditor stdout SHA-256: `0EDBDF8FE7241741386651AAA250BD8B6F263491B6C0156BA720F58725360E38`. Both stderr streams were empty (SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`).
- Docker Desktop and its backend processes were present, but the bounded `docker info` probe did not return; the shared container slot was reserved by another allocation. No container invocation is claimed; this was host-only.

Reproduce construction checks with `python -B -m unittest -v test_method.py`, then (only for a fresh reproduction, not the consumed formal allocation) run `python -B candidate.py --input scenarios.json --output candidate.json` and `python -B audit.py --input scenarios.json --certificates candidate.json --output audit.json`.
