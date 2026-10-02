# Issue #6121 — T0-02 finite successor result

## Outcome

**PASS_METHOD_SCOPED.** A distinct, no-model synthetic finite T0 successor ran in a pinned OrbStack Docker container. Its independent auditor accepted all 20 policy/case runs and six obligation events with zero discrepancies. The prior T0 STOP in PR #6149 is preserved unchanged and was not retried.

## Frozen hypothesis and decision gates

See `PROTOCOL.md` for H/T/D/C/U, frozen semantics, and scope. The near-saturated fixture compares LEDGER_ONLY, GLOBAL_WAIT, FIXED_CAP2, and CLASS_AWARE under identical finite resources and offered task mix. Five cases cover near-saturated burst/drain, below-capacity service, above-capacity burst, missing effect oracle, and unknown capacity. Mandatory releases use a separate lane and must complete at tick 0. A transfer, crash, or timeout does not discharge a system obligation; failed compensation creates a child.

## Results

In the near-saturated synthetic case, CLASS_AWARE recorded max system backlog 3 vs 4 for LEDGER_ONLY, max age 1 vs 2, and five verified effects vs three under GLOBAL_WAIT. It deferred A2. GLOBAL_WAIT deferred A2, B1, RO1, B2, RO2, and RO3. All four policies serviced mandatory REL1 at tick 0.

On the below-capacity control, CLASS_AWARE was `FEASIBLE_SERVICE_REGION` and verified all three effects. The above-capacity case was `SATURATED_BUT_CONTAINED`; the missing-oracle case was `UNRESOLVABLE_ORACLE_GAP`; unknown service capacity was `UNKNOWN_CAPACITY`. None is interpreted as asymptotic stability.

The event-ledger replay ended with P verified terminal and child C pending; system-wide pending count remained one. Owner crash, accepted handoff, and timeout did not reduce it. Failed compensation raised pending count to two before verified disposition of P reduced it to one.

Independent audit: `PASS_METHOD_SCOPED`, 5 cases, 20 policy runs, 6 events, errors `[]`. Construction tests: 11/11 pass; Python bytecode compilation passed. `SHA256SUMS` verifies every listed source and raw output.

## Reproduction and resource boundary

Candidate invocation: `python3 candidate.py fixture.json run/candidate.json`.

Auditor invocation: `python3 audit.py fixture.json run/candidate.json run/audit.json`.

Construction tests: `python3 -m unittest -v test_t0_02.py`.

Formal environment: OrbStack Docker Engine 29.4.0, linux/arm64; image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; containers used `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --cpus=0.5 --memory=256m --pids-limit=32`. The frozen test package ran inside this boundary. No model, GUI, network, live effect, or external service was used. Obstac was not available in this session, so OrbStack Docker was used.

This is an exact finite synthetic-method result only. It does not establish production arrivals, service rates, oracle availability, asymptotic stability, runtime integration, or user benefit. The T1/live gate remains unperformed and separately gated.

