# Issue #5311 T0 A01 result — 2026-10-09

## Disposition

**`FAIL_COST_GATE_SCOPED`** for the frozen minimal certificate schema. The independent audit passed, and the certificate gate rejected every directed invalid certificate, but the required checker-work reduction did not occur: on the eight valid plans, full reconstruction used 80 counted inspections and certificate admission used 136 (70% more). This does not support H for this schema and finite corpus.

## Results

| Gate | Result |
|---|---:|
| Valid plans accepted, full reconstruction | 8/8 |
| Valid plans accepted, certificate admission | 8/8 |
| Invalid certificates rejected, certificate admission | 7/7 |
| Unsafe certificate admissions | 0 |
| Valid-plan effect-label mismatches | 0 |
| Valid-plan checker inspections, full reconstruction | 80 |
| Valid-plan checker inspections, certificate admission | 136 |
| Candidate / independent auditor | exit 0 / exit 0 |
| Audit reconstruction | 15/15 rows; zero errors |
| Retries | 0 |

The 136 inspections consist of the same per-action predicate checks plus certificate-claim checks. A plan digest establishes byte-level binding to a plan, but does not itself prove that each action satisfies a policy predicate. Because this minimal certificate language has no sound compression rule, the checker still inspects every action and adds certificate validation. Three certificate-only mutations leave the underlying plan valid, so full reconstruction admits those plans while certificate admission rejects the malformed certificates; this expected distinction is not counted as an unsafe certificate admission. On the eight valid plans, both gates produce identical effect labels.

## Scope and limits

The corpus and policy are hand-authored and finite; checker cost is a predeclared count of explicit policy-field inspections, not elapsed time. Hashing, serialization, proof production, external verification, atomic check-to-dispatch, and post-action effect verification are excluded. The result does not establish a general impossibility for proof-carrying admission, a proof-system soundness result, live evidence freshness, GUI behavior, action safety, release, product performance, or user benefit. A successor would require a separately specified proof rule that compresses checks without trusting producer assertions; this allocation is consumed and was not rerun.

## Retained evidence

See the frozen [protocol](PROTOCOL.md), [FREEZE.json](FREEZE.json), one-shot [candidate output](results/candidate.json), [candidate stdout/stderr/exit](results/), and [independent audit](results/audit.json). `RUN_RECORD.md` records exact commit, commands, environment, hashes, and dispositions.
