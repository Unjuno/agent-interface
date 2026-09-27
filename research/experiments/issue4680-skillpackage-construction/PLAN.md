# Issue #4680 deterministic SkillPackage construction rung

## H / T / D / C / U

- **H (rung hypothesis):** An externally inspectable deterministic SkillPackage compiled from the existing guarded-macro contract can preserve its bounded decisions, required YIELD/NO_ACTION behavior, intent/generation binding, and immutable ACTIVE/candidate switching on a finite replay fixture.
- **T:** In a network-disabled local Docker container, compare a newly implemented SkillPackage executor against a separately coded oracle over nominal toggle, linked two-step field/save, same state/different intent, forbidden, ambiguous, stale generation, already-satisfied, one local correction, and authority-narrowing cases. Test invalid-candidate rejection and rollback. No user desktop, model, adapter, provider, input, training, or GPU.
- **D:** Scoped construction PASS only if all ten frozen rows match exact expected proposals and effects; the linked field/save steps preserve order; proposals are subsets of package∩runtime authority; invalid candidates preserve byte-identical ACTIVE; rollback restores exact bytes; independent raw auditor has zero errors and rejects all four copied-evidence mutations. Otherwise report the typed failure. This does not adjudicate #4680's full hypothesis.
- **C:** Source contract is the 7-case guarded-macro baseline retained by #4204 (`CASES.json` blob `4250f1bf5429907234aca2e0a5c6c714db3daaa1`), whose independent audit records 7/7 baseline cases and zero model decisions. This rung uses a hand-encoded bounded subset/extension for correction and narrower runtime authority; it is not labeled Astra-authored or adapted Needle knowledge. #4205 remains `HOLD_PROTOCOL_DEVIATION`; no fit/evaluation is repeated. #4670 remains a prerequisite if learned semantic branching is chosen.
- **U:** No adapted-skill provenance, model comparison, speedup, amortization, broad GUI/task correctness, authority promotion, or full #4680 PASS. This tests package/executor construction only.

## Frozen identity and execution

- Allocation: `issue4680-skillpackage-construction-20260927-01`.
- Intake main: `407bea640ad46827f58bd7e30979e52096fff092`.
- Additive local path: `scratch/issue4680-skillpackage-construction/`.
- Container: cached `python:3.11-slim`, local Docker Desktop linux/amd64, `--network none`, 1 CPU, 256 MiB RAM, 32 PIDs, read-only root, 16 MiB noexec/nosuid `/tmp`, no-new-privileges, all caps dropped; source mounted read-only; fresh output only writable.
- Formal rows: exactly 10; no optimizer/model invocations; no retries or tuning.
- Source, fixture, runner, auditor hashes are frozen in `FREEZE.json` before the run.

## Pre-run harness stop (retained)

The first attempted `docker run ... /bin/sh -c ...` command failed with `/bin/sh: Syntax error: Unterminated quoted string` at shell parsing. Docker returned before the container test sequence started; no case ran and no formal result was produced. Corrective change: use a frozen Python orchestrator as the container entrypoint, avoiding nested PowerShell/sh quoting. This is a wrapper correction before the single test invocation, not a research retry.

