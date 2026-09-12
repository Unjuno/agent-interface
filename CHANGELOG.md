# Changelog

## 0.0.1-research.1 — Research Preview 1

Initial public research snapshot.

### Included

- Real-app v1 harnesses for XTerm, Chromium, LibreOffice Calc, and Inkscape.
- Input-delivery experiments separating OS event delivery from application consumption.
- Real-app v2 semantic-method vs optimized-route lifetime experiments.
- Real-app v3 Guarded Hierarchical Deoptimization experiments.
- Raw summary CSVs and detailed research reports.
- Public architecture notes and research methodology.
- GitHub Pages landing page.
- GitHub Actions workflow for prerelease research snapshots.

### Current promoted research conclusions

- Universal control remains the fallback floor.
- Semantic methods and optimized routes should have separate lifetimes.
- Binding repair should not automatically invalidate semantic methods.
- Observable stale-route dependencies should be guarded before executing an expensive failure path.
- Route reheating after two clean fallback uses remains the current baseline.

### Not included / not claimed

- production-ready agent runtime;
- automatic general method discovery;
- cross-platform correctness;
- end-to-end LLM/token benchmarks;
- stable protocol guarantees.
