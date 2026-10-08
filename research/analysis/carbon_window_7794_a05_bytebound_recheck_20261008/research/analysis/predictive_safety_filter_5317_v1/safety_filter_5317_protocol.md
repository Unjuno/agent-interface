# Issue #5317 first-rung finite safety-filter experiment

## H / T / D / C / U

- **H:** A bounded horizon filter prevents unsafe multi-step prefixes missed by a one-step filter; a viability filter also rejects safe-looking transitions that eliminate every goal/recovery path, while preserving a known safe completion and robustly handling finite bounded uncertainty.
- **T:** Seven deterministic workflows × five policies (`POSTHOC_VERIFY`, `ONE_STEP_FILTER`, `HORIZON_FILTER`, `VIABILITY_FILTER`, `UNKNOWN_FAIL_CLOSED`): two-step forbidden terminal, safe dead end, safe goal, bounded-safe branching, bounded branch with forbidden outcome, missing transition, and stale optimistic model. Horizon is frozen at 2. The no-model simulator uses explicit true and candidate transition graphs.
- **D:** Compare unsafe-prefix, stranded-prefix, goal completion, false block, and authority/effect leakage. Target gates: horizon blocks the two-step forbidden proposal before execution; viability blocks the non-forbidden but unrecoverable dead-end; all sound filters preserve the known safe goal; bounded-safe outcomes remain available to robust filters; missing/stale and bounded unsafe outcomes fail closed; zero authority/effect claims.
- **C:** Host-only Python standard library; deterministic, one process, no GUI, model, GPU, network, or real side effect. This is a constructed finite-state discriminator, not an actual Agent Interface runtime effect.
- **U:** Finite abstract graph only. Does not establish that real transition models are complete/current, that users' safety sets are correctly specified, or that external effects are reversible. No broad safety or product claim.

## Container/resource gate

Current main at intake: `70b69b47845b35afde59c2a5f0b56c6f906c6904`. OrbStack context responds; `docker ps` was empty at 2026-09-30 08:59:45 UTC. Image `python:3.13.5-slim-bookworm` is locally present as `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`. Disk free: 1.4 TiB. However, #5085 has unresolved exclusive GPU/Docker requests and no CPU slot assignment for this Issue. Therefore the planned container rung is **HOLD_NO_EXACT_SLOT**; no container was created. Host execution is kept distinct and does not consume/replace a container allocation.

## Reproduction

`python3 -B -m unittest -v test_safety_filter_5317`

## Host-only result (2026-09-30 09:03 UTC)

- Test command: `python3 -B -m unittest -v test_safety_filter_5317` — 7/7 PASS.
- Matrix command: `python3 -B run_safety_filter_5317.py safety_filter_5317_raw.json` — 7 scenarios / 35 policy cells, host only.
- Independent audit: `python3 -B audit_safety_filter_5317.py safety_filter_5317_raw.json` — `PASS_READONLY`, 35 cells, errors=0.
- `ONE_STEP_FILTER` admitted the two-step unsafe prefix and the true graph reached `BAD`; `HORIZON_FILTER` rejected that proposal before execution.
- `ONE_STEP_FILTER` and `HORIZON_FILTER` admitted the safe-but-stranded dead end; `VIABILITY_FILTER` rejected it.
- All policies preserved the exact safe goal. Robust filters admitted the bounded-safe branch; the deliberately uniform `UNKNOWN_FAIL_CLOSED` arm false-blocked it. Bounded-with-BAD, missing, and stale cases failed closed for predictive filters.
- Raw SHA-256: `fef9450c33cd227f794d6146a88fea7c89fad31b1758e800bff04d796935e611`.

Disposition: **PASS_HOST_FINITE_DISCRIMINATOR_SCOPED / HOLD_NO_EXACT_SLOT_FOR_CONTAINER_RUNG**. These outputs are host-only evidence, not a substitute for the requested OrbStack run. Do not relabel as container evidence. If a fresh exact slot is granted, run one network-disabled/read-only container against the frozen source/image, perform a separate raw-only audit, and retain it as a distinct container receipt without overwriting this host raw. Full-result promotion remains scoped to this finite abstract graph.
