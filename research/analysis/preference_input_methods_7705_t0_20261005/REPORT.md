# Issue #7705 T0 — synthetic method contract

**Disposition: `PASS_METHOD_SCOPED`.** The independent auditor exactly reconstructed all eight cases, Pareto membership, eligibility and typed selections with zero errors. It rejected all four preregistered mutations: wrong unit, omitted criterion, reversed objective direction, and hard-gate-failing route promoted as eligible.

## H/T/D/C/U

**H.** A method-only evaluator can preserve hard eligibility and distinguish a unique selection, an ambiguous set, an impossible aspiration, and incomplete input without pretending that every preference identifies one best route.

**T.** Eight finite cases covered numeric weights; attainable and impossible aspirations; duplicate vectors/ties; pairwise selection; missing criterion; convex and disconnected Pareto fronts. Candidate and independent auditor each ran once on CPython 3.14.5/macOS arm64; two construction tests passed before freeze.

**D.** PASS_METHOD_SCOPED: eight outputs match the independent oracle; zero errors; four of four mutations rejected.

**C.** Common fixed objective directions/units and hard eligibility across modes. Duplicate objective vectors retain distinct route IDs, and the Pareto set is reported separately from preference selection.

**U.** Synthetic evaluator contract only. No participant/usability/fidelity evidence, measured route vectors, live selector, product recommendation, safety or adoption result.

## Reproduction

One-shot commands are `python3 -B candidate.py` and `python3 -B auditor.py`. Raw outcomes and receipts are in `formal_01/`; frozen inputs are in `FREEZE.json`. No retries.
