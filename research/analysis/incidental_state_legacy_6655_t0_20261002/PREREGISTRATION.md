# Issue #6655 incidental-state legacy T0 — WSLc successor

This is a runtime-conforming successor to the consumed host allocation; it does not edit, replace, or reinterpret its raw result. Scope remains a finite synthetic method test only: no real interface, GUI, model, user/workspace state, network, GPU, or external effect.

## H / T / D / C / U

- **H:** The finite synthetic scorer distinguishes helpful incidental state, harmful stale state, irrelevant state, required effects, and ineligible shared/incompletely-restored state; an independent auditor reconstructs all 224 rows and rejects frozen protocol mutations.
- **T0:** Run the immutable source/input snapshot with the exact local WSLc image in `FREEZE.json`, pull disabled, network none, CPU 1, memory 512m. First run the 9-test construction suite. Then invoke one candidate and one separate raw-only auditor, no retries or tuning. Freeze hashes/commands and prove outputs absent before formal invocations.
- **D:** `PASS_METHOD_SCOPED` only if construction passes 9/9, candidate exits 0, separate auditor reconstructs all 224 rows with zero errors, and independent mutations are rejected. Else report exact STOP/FAIL/HOLD. No live-interface claim.
- **C:** Tests deterministic scorer and runtime reproduction only, not user benefit or causal transfer.
- **U:** Synthetic cases omit actual application timing, state ownership, concurrency and restoration behavior; observed WSLc enforcement is not generalized beyond recorded checks.

## Runtime

WSL native `wslc` only (WSL 3.0.1.0), using the immutable local image digest in `FREEZE.json`, `--pull never --network none --cpus 1 --memory 512m`. No Podman, Docker Engine, GPU, external data, or network. Source mount read-only; only a dedicated fresh result directory writable. Construction command and candidate/auditor command templates are pinned in the freeze. Candidate and auditor caps are 1 each; retries 0.

The original allocation `INCIDENTAL-STATE-LEGACY-6655-T0-20261002-01` ran on Windows host in protocol deviation (1 candidate/1 auditor); preserve its output and classification unchanged. This successor uses a new output path and allocation ID.
