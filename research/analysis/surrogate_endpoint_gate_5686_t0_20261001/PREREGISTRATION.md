# Issue #5686 T0 preregistration

Status: synthetic method-construction experiment; no empirical interface result.

## H / T / D / C / U

- **H:** a rule that promotes an interface change whenever its intermediate metric improves will false-promote at least one finite control. A gate that also requires an independently scored final outcome, preserves adverse safety outcomes, and refuses missing endpoints will reject those controls while retaining a consistent positive control.
- **T:** enumerate paired potential outcomes for two named task/route strata in four frozen worlds: (1) concordant intermediate and final effects, (2) intermediate-only effect, (3) within-arm common-cause association without a treatment effect on the final endpoint, and (4) surrogate-paradox direct harm. Add an incomplete-endpoint world with an unfinished attempt. Emit every attempt and stratum label. Candidate computes effects and gate dispositions; an independent raw-only auditor recomputes them from JSONL without importing candidate code.
- **D:** `PASS_SURROGATE_GATE_SCOPED` only if all five worlds have the preregistered expected contrasts/dispositions, the concordant control is retained only as `DIRECTION_CONCORDANT_IN_OBSERVED_STRATA / PREDICTIVE_VALIDITY_UNESTABLISHED`, false-promotions/inversions/harm/missingness are not promoted, and the independent audit agrees. This is not empirical validation of any metric.
- **C:** finite authored potential outcomes test logical behavior, not sampling error, measurement validity, interference, adaptive policies, external transport, or whether these controls span real interface failures.
- **U:** no causal or product claim; no old data are used or changed. A synthetic pass is only a test of this gate's behavior on these fixtures.

## Frozen execution contract

- **Execution-context amendment before formal invocation:** the requested local OrbStack slot is withdrawn, candidate/auditor/container count remains zero. The current shared-host ledger records four nonterminal Created containers with unresolved ownership and an A07 `STOP_RESOURCE_COORDINATION_BEFORE_CANDIDATE`. Per the queue rule, no unrelated container is inspected or changed. Local development/CI remains on this Mac; formal candidate and auditor run as distinct bounded Docker containers on isolated GitHub-hosted runners. The hypothesis and decision rule are unchanged.
- Base: current `main` is read and frozen immediately before workflow dispatch.
- Source: package sources, tests, fixture, and the workflow; SHA-256 recorded in `FREEZE.json` before dispatch.
- Formal allocation: `SURROGATE-ENDPOINT-GATE-5686-T0-GHA-20261001-01`; the first push creating the frozen branch triggers the one-shot workflow and binds exact branch head and main SHA. Subsequent pushes fail closed; no same-allocation retry.
- Candidate container: `python3 candidate.py --input fixtures.json --output candidate.jsonl` in a digest-pinned Python job container.
- Auditor container: separate digest-pinned job; `python3 audit.py --input candidate.jsonl --fixtures fixtures.json --output audit.json`. It reads candidate JSONL and the frozen fixture, never candidate code.
- Environment: `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, verified as `linux/amd64`; candidate and audit use distinct GitHub-hosted Docker containers/runners with `--network none`, read-only source mounts, and bounded CPU/memory/PIDs. No retries. Host-native tests are development checks, not formal container results.
- Raw evidence: exact stdout/stderr, JSONL, auditor JSON, command/environment manifest, hashes, and exit codes retained under `raw/formal/`.
- Any main/source/hash drift, wrong dispatch input, missing pinned image, nonzero candidate, audit disagreement, or artifact collision is STOP; no rerun under the same allocation.

The candidate and auditor must each validate their input schema and retain all attempts. The auditor may not import or execute candidate code. Hard-safety regression is never averaged away. No real surrogate may be promoted from this T0.
