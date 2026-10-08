# Issue #8598 T0 A01 — censored opportunity tail regret

This package evaluates a finite synthetic proposal from Issue #8598. It is CPU-only and deliberately does not use Docker/WSLc, a model, humans, GUI, network, or a live allocation.

## State

Construction and preregistration are complete and digest-bound by `FREEZE.json` / `SHA256SUMS`. At that freeze commit, formal candidate and auditor invocations had not occurred. The report placeholder is not a result. Do not interpret construction tests as the formal study outcome.

## Package map

- `PROTOCOL.md` — H/T/D/C/U, estimands, decision criteria and custody.
- `build_fixture.py` — deterministic public/hidden fixture generator.
- `candidate.py` — observable-only resolved, known-propensity IPCW/Hájek and partial-envelope summaries.
- `auditor.py` — truth-side prefix and exact-summary reconstruction using an independent Rockafellar–Uryasev expected-shortfall formulation.
- `test_*.py` — construction and adversarial audit tests.
- `inputs/` — pre-run frozen public and hidden input bytes.
- `raw/` — one-shot formal process outputs and stdout/stderr/exit records.
- `REPORT.md` — final disposition and scope after the one-shot candidate/auditor chain; created before formal freeze so the generated result index can be validated on the complete checkout.

## Construction feasibility signal

The first preregistered rule required at least 80% correct IPCW tail ranks and a 10-point gain over resolved-only in the correctly specified recorded-covariate arm. Construction evaluation disproved that threshold on the deterministic fixture, so the rule was amended before any candidate/auditor formal invocation: the absolute 80% gate remains and IPCW must strictly outperform resolved-only. A second pre-freeze feasibility test also failed the amended criterion (10/128 strict IPCW-correct versus 20/128 resolved-only-correct). This adverse signal is retained and the final gate is not loosened further. The latent-severity arm's declared .70 value is deliberately not the actual completion model; its IPCW output is descriptive only and is not used as evidence of adjustment under correct assumptions. No result is formal yet.

## Run custody

Candidate and auditor each run at most once from the freeze commit; outputs must not preexist. A candidate failure or audit HOLD is retained without retry. Formal output is not eligible to support any live/product/safety claims.
