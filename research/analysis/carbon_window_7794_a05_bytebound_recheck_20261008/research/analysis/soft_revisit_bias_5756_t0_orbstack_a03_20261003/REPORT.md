# Issue #6442 / #5756 — OrbStack A03 result

## Disposition: `PASS_METHOD_SCOPED`; no soft-specific advantage demonstrated

One fresh allocation was frozen against current main `fa791fe937fb24245e785d9e22928b3f4a6a42ae`, then executed once in OrbStack and audited once. A01 and A02 remain unchanged pre-candidate STOPs; no earlier candidate or auditor was rerun. See `FREEZE.json`, `PREREGISTRATION.md`, and the command record in `RUNBOOK_A03.md`.

### H / T / D / C / U outcome

- **H:** The bounded soft revisit policy recovers targets following incomplete inspection or a same-epoch revision cue, while avoiding stable/complete revisits. Its unique value over a stateless cue policy is separately gated.
- **T:** 32 frozen synthetic fixtures × four policies = 128 rows; max 12 events per row. Candidate source was nine exact Git-blob-associated source files from the prior preserved package on the pinned main. The pinned Python image digest ran on `linux/arm64`, offline, with `--cpus 0.25`, `--memory 512m`, and UID/GID 65534. Source and audit input were read-only; candidate and audit used separate output directories.
- **D:** Construction container exit 0, `memory.max=536870912`, 13/13 construction tests passed. Candidate produced 128 rows; OrbStack event record confirms container exit 0. Independent raw-only auditor exit 0 reconstructed all 128 pairs with `errors=[]` and `PASS_METHOD_SCOPED`. All preregistered summary/safety gates passed.
- **C:** In the partial/revision stratum, success counts were soft 16/16, stateless 16/16, hard exclusion 0/16, and exhaustive DFS 0/16. Therefore soft-minus-hard=16, soft-minus-stateless=0, soft-minus-exhaustive=16. Stable/complete success was 8/8 for every policy; stable soft revisits=0. No-target false claims=0; forbidden traversals=0; stale-epoch acceptance=0. The observed tie means this schedule supports comparison against hard exclusion but **does not demonstrate that the soft revisit bias adds value over stateless ranking**.
- **U:** Deterministic authored finite fixture only; no GUI, model/LLM, human, GPU, external effect, natural hierarchy distribution, latency, general search optimality, safety guarantee, or live task-transfer evidence. `memory.max` was observed; swap-limit enforcement was not measured or claimed.

## Execution / audit record

- Construction: one OrbStack container; exact cgroup memory cap observed; 13 tests passed; output in `CONSTRUCTION.log`.
- Candidate: one invocation; 128 rows in `candidate/raw.jsonl`; SHA-256 `c13a98c8b5840697b410e093f4132b9f9b314c8893d1cf6f32a4b889924edbfa`.
- Audit: one distinct container; candidate input mounted read-only; 128 rows, zero errors; SHA-256 `91a5c91ff061a11c0f0e75a0bbbd13db984a345c98653208097de3c927293e76`.
- Retries: 0. Candidate/Audit container event logs independently record `exitCode=0`; full container IDs are retained in the `.container-id` files.
- **Runner-wrapper deviation:** after the candidate container had returned, a zsh post-run logging assignment used the reserved read-only variable name `status`, making the outer shell exit 1 before it printed its captured pipeline status. The candidate itself emitted its completion record and 128-row file; the OrbStack event stream independently confirms the candidate container's `exitCode=0`. The candidate was not repeated. The audit wrapper used a nonreserved variable and exited 0.
- **Shared-engine boundary:** the read-only inventory before and after showed another owner's long-running `unjuno-native-ci-6092` container. It was not inspected internally, stopped, or modified. A03 used separate short-lived containers with network disabled and CPU/memory limits on the shared OrbStack Docker engine; no exclusive-engine or timing-isolation claim is made. This experiment has no timed endpoint, so resource contention does not enter its declared estimand.

Raw and audit bytes, logs, image/source freeze, and integrity manifest are retained alongside this report. Historical STOPs remain at their original paths and were not edited.
