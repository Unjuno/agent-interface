# Issue #8152 T0 protocol (frozen before formal execution)

## H/T/D/C/U

- **H:** On the frozen finite stochastic event model, repeated authority-preserving reduction returns shorter legal traces with exact-target held-out recurrence non-inferior to the original by at most 0.20, and sequential screening uses fewer search calls than fixed-64 screening. Single-run screening is expected to be less stable.
- **T0:** Standard-library CPU-only deterministic hash oracle. Twelve instances span four predeclared strata (three instances each); target and competing fingerprints share exit code 17. The typed DAG includes mandatory reset/lease/release ancestry and causal-closed removal groups. A/B/C are single-run, fixed-64, and sequential 8..64 in batches of eight. Each instance has 64 baseline search trials and 512 paired held-out confirmation seeds, disjoint from search. Candidate and auditor are separate offline containers. The audit reconstructs every outcome from raw events/seeds and recomputes exact one-sided Clopper-Pearson limits. Per-instance non-inferiority uses Bonferroni-adjusted simultaneous bounds: final lower minus original upper must be at least -0.20. This is conservative but has familywise coverage at least 95% across the 12 instance comparisons.
- **D:** `METHOD_PASS_SCOPED` only if all accepted traces retain reset/lease/release and DAG legality, raw search and confirmation reconstruct exactly, both statistical arms (fixed-64 and sequential) pass held-out target-fingerprint non-inferiority in every instance, competing-fingerprint controls never count as target, confirmation seeds are disjoint, and sequential search calls are fewer than fixed-64 while shrinking at least one trace. A is a deliberately unprotected one-run comparator and is reported, not a required pass arm. Any authority violation, fingerprint confusion, malformed evidence, or false non-inferiority is `FAIL_METHOD`; sparse/uncertain evidence or no eligible shrink is `HOLD`.
- **C:** Deterministic replay or fixed repetitions may be more reliable; the observed variation may not be reducible nuisance history.
- **U:** This finite stationary hash model does not establish a live GUI failure's reproducibility, causal root cause, minimality beyond this grammar, irreversible-effect safety, or production utility. No existing failure is replayed.

## Frozen controls

Construction tests remove lease/release, make the competing fingerprint share the target exit code, overlap a search seed with confirmation, alter a frozen threshold, and delete a raw attempt row; the auditor must reject each relevant corruption. Tests never invoke the formal candidate. `results/` is empty at formal start. The formal runner performs one candidate invocation followed by one independent audit invocation; neither is retried.

## Environment

Image: `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151` (linux/arm64). Use the direct OrbStack CLI, `--pull=never`, `--network=none`, read-only root filesystem, no capabilities, no-new-privileges, bounded CPU/memory/pids, and a writable mount only for `results/`. No model, GUI, GPU, network, Docker daemon calls from candidate, or user data.
