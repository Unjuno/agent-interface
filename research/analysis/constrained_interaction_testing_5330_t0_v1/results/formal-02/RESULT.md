# T0 result — Issue #5330, separate allocation 02

Disposition: **`PASS_DESIGN_SENSITIVITY_ONLY`**, followed by **`PASS_AUDIT`**. The previous allocation 01 `STOP_RUNNER_IMPORT_ROOT` remains preserved in `../formal-01/` and was not overwritten or retried.

## Outcome

| Design | Cases | Pair coverage | Planted pair detected? | Triple coverage | Planted triple detected? |
|---|---:|---:|---|---:|---|
| OFAT | 5 | 18/24 | No | 16/32 | No |
| Pairwise | 6 | 24/24 | Yes | 22/32 | No |
| Three-way | 8 | 24/24 | Yes | 32/32 | Yes |
| Exhaustive | 16 | 24/24 | Yes | 32/32 | Yes |

The deterministic pairwise design exercised 1.5× as many rows as OFAT (6 vs 5) and found the deliberately planted freshness×lease pair that OFAT missed. The three-way design exercised 8 rather than 16 exhaustive rows and covered all binary triples, finding the deliberately planted freshness×responsibility×delivery conjunction. This confirms only the sensitivity of these exact designs to these exact finite synthetic oracles. It does not demonstrate empirical hazard discovery or superiority on repository/runtime failures.

## Independent audit

The raw-only auditor exited 0 with `PASS_AUDIT`, `errors=[]`; all four row lists, assignments, pair/triple coverage counts, oracle detections, and case counts reconciled. `AUDIT_SUMMARY.json` records the independently reconstructed values and raw SHA-256.

## Provenance and artifact-path note

Frozen image `python:3.12-slim`, `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (linux/amd64), Python 3.12.14; network off, read-only root, all capabilities dropped, no-new-privileges, research source read-only. Runner and auditor each invoked once; both exited 0. No application/model/GUI/network/external effect.

The host output mount was `results/formal-02/` and the frozen in-container argument was `/out/formal-02`; accordingly the immutable runner artifacts are nested at [`formal-02/raw.json`](formal-02/raw.json) and [`formal-02/summary.json`](formal-02/summary.json). They are retained at their actual first-write path; no post-run relocation or regeneration was performed. Raw SHA-256 `2b103e23b385f49b9d569fe9d12ed834783bca070dcad4a37ca43a201693c9f5` (2,983 bytes). The first failed allocation's STOP evidence remains at [`../formal-01/STOP.json`](../formal-01/STOP.json).

## Scope limits

The design factors were assumed independent only to form this binary fixture. Both positive controls were planted by construction. Nothing here estimates real failure prevalence, validates metamorphic relations, ranks practical interaction strengths, establishes safety, or tests constrained designs against authentic Agent Interface hazards. A future rung should derive dependencies and oracles from a concrete, sandboxed repository workflow and independently justify them before claiming practical utility.
