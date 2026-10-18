# Issue #8635 T0 A01 — preregistration draft

**Lineage:** fresh successor to #8629's `HOLD_CANDIDATE_ENTRYPOINT_NAMEERROR`; no edit or rerun of that allocation.
**Allocation:** `EPISTEMIC-ACTION-8635-T0-A01-20261008`
**Base main:** `76eefd0e53da2243d1e2ab45776db7761f4366ee` (refreshed before publication; refresh again before formal freeze)
**Formal status:** not frozen; candidate/auditor invocations 0/0. Construction suite currently 22/22 under normal CPython and `-O`; the pre-freeze missing-executable path is tested as a retained HOLD receipt.

## H / T / D / C / U

- **H:** On a fresh finite synthetic held-out family, independently implemented deterministic policies with planted recognition, action-selection, evidence-use, and stopping defects will have distinguishable competency profiles that aggregate task success can conceal, without hard-gate violations. This probes the measurement method, not general model competence.
- **T:** Use fresh seeds 59/71/83/97 × six authored evidence strata × two repetitions (48 cases). Compare five policies across PRESCRIBED, AVAILABLE, and NO_EPISTEMIC_ACTION (720 rows). Candidate input excludes generator labels and oracle outcomes. A separately written raw-only auditor reconstructs case-policy-arm rows and evaluates four preregistered corruptions. A new CLI integration test must launch the actual candidate script and verify valid JSON, schema, 720 rows, uniqueness, exit 0, and empty stderr before the source freeze. Formal candidate and auditor each run once in separate WSLc containers using the already cached Python image pinned as `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network disabled, pull disabled, one CPU requested. No memory-cap efficacy is claimed.
- **D:** Construction gate requires 22/22 tests under normal and `-O`, including real candidate and auditor CLI subprocess tests, WSLc command/staging contracts, and a synthetic executable-launch failure that must leave a 0-invocation HOLD receipt without starting the auditor. Formal method PASS requires complete held-out binding, independent reconstruction of all 720 rows, and rejection of all four controls. H_PASS_SCOPED additionally requires each planted defect detected, STOPPING_DEFECT sharing reference aggregate task success but scoring worse on stopping, and zero hard-gate violations. Candidate/auditor process failures retain exact bytes, no retry, and no scientific inference from absent output.
- **C:** All policies, task strata, outcome labels, and oracle rules are authored in one packet. Separate modules and raw-input custody do not equal blinded external authorship. Seed changes vary identifiers/provenance, not the six underlying semantic strata.
- **U:** Finite deterministic synthetic method evidence only. No LLM, learned-agent, human, GUI, runtime safety, privacy, latency, user-benefit, or product conclusion. No external or consequential action.

## Launch gate

The repository's #5085 coordination record contains a continuing WSLc shared-state HOLD requiring explicit reconciliation and a named allocation before further WSLc invocations. No formal launch is authorized by an idle inventory snapshot. Keep candidate/auditor invocation counts at 0/0 until that gate is reconciled; do not silently substitute host Python or Docker Desktop for the preregistered WSLc execution.
