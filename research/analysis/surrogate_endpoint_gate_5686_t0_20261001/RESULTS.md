# T0 formal result

## Outcome

Allocation `SURROGATE-ENDPOINT-GATE-5686-T0-GHA-20261001-04` completed the preregistered finite synthetic gate on 2026-10-01. The candidate and independent auditor each exited 0 in separate, network-disabled, digest-pinned Docker containers on separate GitHub-hosted jobs. The formal result is **`PASS_SURROGATE_GATE_SCOPED`**.

This establishes only that the frozen gate behaved as specified on its authored finite controls. It does not validate any empirical interface metric as a surrogate, establish a causal/product effect, or authorize runtime policy promotion.

## Frozen experiment and artifacts

- Issue: [#5686](https://github.com/Unjuno/agent-interface/issues/5686)
- Workflow: [run 36807980580](https://github.com/Unjuno/agent-interface/actions/runs/36807980580)
- Branch head: `5dc69a27e68c8d6b2492529c83107b6130978114`
- Frozen base main: `a7648fb47f16b15ac2fdb63075186aad1189859c`
- Image: `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`
- Observed image ID: `sha256:febd0be41adb897a0ab8f1f1c693d8912669ea60c4940e076e9946b60e210ef0` (`linux/amd64`)
- Candidate: 24 attempt rows across five authored worlds and two strata; exit 0. JSONL SHA-256: `d0f584018babafe1c1797f5fe64f76d8a890bd310220d3be14a9cb51964e30df`.
- Independent raw-only audit: exit 0; `PASS_SURROGATE_GATE_SCOPED`, zero errors. JSON SHA-256: `30603d4f6263581caa28866324268a3bddfce8097aa493028a27416ea8799342`.
- A second local audit of the downloaded formal JSONL reproduced the formal audit JSON byte-for-byte.
- Full runner logs, start-gate records, candidate JSONL, audit JSON, image evidence, exit codes and container IDs are retained under `raw/formal/allocation-04/`.

## Decision boundary

The five frozen dispositions were:

- `concordant` → `DIRECTION_CONCORDANT_IN_OBSERVED_STRATA_PREDICTIVE_VALIDITY_UNESTABLISHED` (4 attempts).
- `unrelated` → `REJECT_INTERMEDIATE_ONLY_EFFECT` (4 attempts).
- `common_cause` → `REJECT_INTERMEDIATE_ONLY_EFFECT` despite naive intermediate-only promotion (8 attempts).
- `paradox` → `REJECT_NONCOMPENSABLE_SAFETY_REGRESSION` (4 attempts).
- `incomplete` → `UNCERTAIN_INCOMPLETE_ENDPOINTS` (4 attempts).

All attempts and both strata (`route_a`, `route_b`) were retained. No empirical task, model, GUI, or historical result was used.

## Predecessor execution history

Earlier unique allocations are retained without retry or outcome laundering: -01 STOPped before container start on main drift; -02 STOPped before container start because shallow checkout omitted the frozen git object; -03 started the candidate container but exited 1 on a bind-mount permission error before producing candidate data. All three had scientific status `NOT_EVALUATED`. Allocation -03 raw failure artifacts are retained at `raw/formal/allocation-03/`.
