# Successor allocation: independent effect oracle v2

## H / T / D / C / U (frozen before execution)

- **H:** An independent, stdlib-only replay oracle can apply the previously frozen deterministic SkillPackage proposals to a separately implemented settings-state model and reproduce all expected postconditions, including staged multi-step save, while rejecting corrupted proposal/effect/result evidence.
- **T:** Audit the retained result from allocation `issue4680-skillpackage-construction-20260927-01` without rerunning its proposer, formal runner, or auditor. Ten frozen rows, exact case/package/source identities. Apply only three pure transitions: toggle visible boolean; stage a supported field value; save the staged field. YIELD/NO_ACTION are no-ops. Compare exact proposal and persistent postcondition; verify the linked SET_FIELD→CLICK sequence.
- **D:** PASS only if all ten raw proposals exactly match frozen expected proposals, all ten independently simulated persistent postconditions exactly match the fixture labels, the multi-step link is valid, source/raw hashes match, and four distinct corrupted evidence copies are rejected. Any mismatch is FAIL; missing evidence/container is STOP. No retry or modification of the predecessor allocation.
- **C:** Same immutable 10-case settings fixtures, same deterministic package and proposals from predecessor allocation #4680. No model, optimizer, GUI, host input, external network, GPU, or learned backend. The oracle is separately authored and imports none of the proposer/auditor code.
- **U:** This can validate only deterministic proposal-to-fixture transition consistency. It does not establish real application effects, Astra demonstrations/adaptation, Needle quality, semantic backend quality, speed, amortization, broad task correctness, or full #4680 success.

## Execution constraints

One local Docker invocation, `python:3.11-slim` pinned by local image ID at freeze time, network disabled, 1 CPU, 128 MiB, 16 PIDs, read-only root and input, bounded tmpfs, no capabilities. Source/raw predecessor artifacts mounted read-only; only a fresh output directory writable. The existing consumed runner allocation is never rerun.

## Decision handling

Freeze this plan, source and predecessor artifact hashes before the Docker invocation. Preserve first outcome verbatim. Do not tune, retry, relabel, or amend predecessor files/results. Publish the full successor bundle additively and link it from Issue #4680.

