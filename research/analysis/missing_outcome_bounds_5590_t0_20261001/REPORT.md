# #5590 finite-cohort missing-outcome bounds — T0 report

## Disposition

`PASS_BOUNDS_SCOPED_HOST_ONLY` for the declared deterministic synthetic cohort. The separate requested container rung remains `NOT_RUN`: allocation `COMPETING-RISK-AJ-CENSORING-5590-T0-20261001-03` was consumed by a cross-context preflight STOP; it is not reused by this experiment.

## Hypothesis and test

H: On a frozen cohort with unresolved outcomes, sharp no-assumption success bounds can prevent an observed-only promotion unsupported by every ledger-compatible completion.

The frozen ledger has 10 launched synthetic episodes: 6 verified successes, 1 verified failure, and 3 unresolved outcomes with explicit reasons. Threshold `tau=3/4`. The candidate enumerates all `2^3=8` binary completions. A separately written raw-only auditor recomputes from the input ledger, checks the full completion power set, exact rational bounds, decisions, identities and denominator. Construction tests include denominator omission, outcome relabeling, duplicate IDs, boolean threshold and duplicate completion mutations.

## Executed evidence

- Host T0 base main: `e32ace71fa1158ca8d5eec13fe620a1a51c1ff00` (the tested local sources and ledger are independently pinned by their exact SHA-256 values in `FREEZE.json`).
- Host: CPython 3.14.5, macOS arm64; standard library only.
- Construction command: `python3 -W error::ResourceWarning -m unittest -v` — **8/8 passed**.
- Syntax command: `python3 -m py_compile candidate.py audit.py test_bounds.py` — **passed**.
- Candidate command: `python3 candidate.py ledger.json results/host-boundary-01/raw.json` — **exit 0**.
- Separate audit command: `python3 audit.py ledger.json results/host-boundary-01/raw.json` — **exit 0**, `PASS_BOUNDS_SCOPED`, `errors=[]`.
- Repository local CI on the then-current `1ecc98b03ed5efeaee2cb664feb6f5e91280389f`: analysis index check; research-workspace test suite **21/21**; workspace index **148 top-level directories reachable**; analysis-index unit suite **6/6**; `git diff --check` — all passed.
- Raw SHA-256: `0f428c7d3da7b29cb982d1d7502536c3f562e569d6e16d18e4e7d37f5e1ed4ec`.
- Candidate stdout SHA-256: `d9d71397f7212f61941cba33cbe3ea7bd31d0cb19b799deb645f87e3a15bed04`.
- Auditor stdout SHA-256: `00cd1f13ba775126aecbab7cc90ac8adf8f1dd062c8a11c7bcf44277095e5e6c`.

## Result

Observed-only rate is `6/7`, which would promote at `3/4`. Assigning every unresolved episode to failure yields `6/10` and does not promote. The sharp no-assumption interval is `[6/10,9/10]=[3/5,9/10]`, which crosses the threshold and therefore gives `PROMOTION_UNIDENTIFIED`. All eight compatible completions were independently reconstructed; the minimum and maximum attain both interval endpoints. The auditor rejected all five declared mutations.

This supports the arithmetic/method contract on this synthetic finite cohort; it does not establish that a real benchmark cohort contains unresolved launched episodes or that any real promotion decision changes.

## STOP and scope boundaries

The earlier `COMPETING-RISK-AJ-CENSORING-5590-T0-20261001-03` slot has inconsistent attached-context records and is retained as `STOP_ALLOCATION03_CROSS_CONTEXT_PROVENANCE_CONFLICT` by the shared queue. No result from that allocation is included here. No Docker/OrbStack invocation occurred in this T0. Before any container portability rung, obtain a fresh unique allocation, reconcile the active OrbStack context and all task owners, refresh main/image/source hashes at the assigned start, and verify there are no active containers. Do not interpret this host PASS as container evidence.

No sampling-confidence interval, missingness model, causal treatment effect, real-agent task effect, scorer validity, population generalization, runtime safety, or product/benchmark qualification is claimed.
