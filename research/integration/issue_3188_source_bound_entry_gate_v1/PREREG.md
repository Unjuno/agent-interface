# Issue #3188 source-bound execution preregistration

## H/T/D/C/U

- **H:** Executing the exact main-branch MAP01 recovery-entry gate source in a pinned local container will produce the declared 32-vector readiness output, and a separately implemented auditor will independently reconstruct all decisions and controls.
- **T:** Allocation `issue3188-source-bound-entry-gate-formal-01`. Freeze main commit, exact candidate source hashes, image digest/platform, command, output schema and decision gates before running. Execute exact `run.py` once in network-disabled OrbStack; audit immutable output in a second network-disabled container using independent code. No CI substitution, source edits, or retry.
- **D:** PASS only for 32 unique Boolean vectors, exactly one AUTHORIZE, current snapshot HOLD, five negative controls HOLD, exact per-row recomputation and all corruption challenges rejected. Source/image mismatch or execution failure is STOP; incorrect rows or controls are FAIL; missing retained bytes is HOLD.
- **C:** Readiness/classifier only. No game, model, GUI, X11, input, authority grant, or recovery efficacy. This is the exact-source/equivalent-local execution rung requested by #3188, not proof of live MAP01 behavior.
- **U:** Does not establish source/workflow equivalence for any absent CI-only wrapper, runtime safety, recovery efficacy, or production readiness.

## Frozen inputs (before allocation)

- Repository: `Unjuno/agent-interface`
- Base commit: `f79ef46d478911170d73b71bddcbe58fd698dc84`
- Candidate paths:
  - `research/analysis/map01_matched_recovery_entry_gate_3008_v2/run.py`
  - `research/analysis/map01_matched_recovery_entry_gate_3008_v2/audit.py`
- Candidate SHA-256:
  - `run.py`: `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822`
  - `audit.py`: `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d`
  - independent verifier: `ffae71aa3546b552915f894fac14d29c9e5d4c7007058941b881e7233e3083d2`
- Image: `python:3.12-slim`, immutable image ID `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9`, RepoDigest `python@sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9` (OrbStack reports Linux/arm64).
- Runtime: OrbStack Docker Engine `29.4.0`, daemon platform `linux/aarch64`.
- Allocation output: `results/formal-01/raw.json`; no pre-existing output.
- Command shape: `docker --context orbstack run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m -v <candidate-dir>:/src:ro -v <formal-dir>:/out:rw <frozen-image-id> python /src/run.py /out`.
- One formal invocation; no same-ID retries, replacements, or threshold changes.

## Independent audit freeze

The independent audit will use the separately written `independent_audit.py`, not import `run.py`, `audit.py`, or either candidate's decision function. It will derive the 32 rows by bitmask and an explicit five-field conjunction, compare exact row identity/order/uniqueness, recompute the five negative controls, and reject five evidence mutations (row bit, row count, independent summary count, expected class label, and source hash). Formal raw is read-only to the audit container; only `results/independent-01/` is writable.

## Expected disposition and limits

Expected readiness snapshot classification is HOLD; the gate's single AUTHORIZE truth-table vector is a logical admissibility state, not a live authority grant. Results will be interpreted only at this finite classifier boundary. Prior #2345 STOP and earlier reconstructed-runner HOLD are immutable historical outcomes.
