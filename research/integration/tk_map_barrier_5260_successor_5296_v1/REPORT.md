# Issue #5296 — Tk mapped-geometry construction

## H / T / D / C / U

The preregistered hypothesis, bounded protocol, and decision limits are in Issue #5296. This is a runner-boundary construction only; it is not the #5260 focus-order comparison.

## Allocation record

- Allocation 01: `tk-map-barrier-5260-5296-20260930-01` — `STOP_WRAPPER_DISPLAY_ARGUMENT_EMPTY`; the WSL shell expanded DISPLAY before `xvfb-run` supplied it. The probe exited before Tk/raw output. See `results/construction-01/STOP_RECORD.json`; do not retry.
- Allocation 02: `tk-map-barrier-5260-5296-20260930-02`.
- Frozen main: `7d7142927fe0359e30a90834846602b3e58c6767`.
- Freeze: `FREEZE-02.json`; probe SHA-256 `8D3C293861684209157DE989DE12FD28B2480E0431CD843FB0651CAE4E6C1C8B`; auditor SHA-256 `637770AF6C15D5ADF0C0A2C87EDF0CD34B38B165EEA7B55F85E44FC36E736C0C`. Both were re-read before launch and matched.
- Exact run: `xvfb-run -a sh -c 'python3 probe.py tk-map-barrier-5260-5296-20260930-02 "$DISPLAY" results/construction-02/raw.json'`; exit 0. One fresh Tk Entry, no XTest or other input. CPython 3.12.3 / Tk 8.6 on Ubuntu WSL2 x86_64.
- Separate raw-only auditor: `python3 audit.py results/construction-02/raw.json results/construction-02/audit.json tk-map-barrier-5260-5296-20260930-02`; exit 0, errors empty. Raw SHA-256 `6f0163026f6e6e08270b63f958636926082cfed347ed2e3ad41dc009446d74d9`.

## Observation / disposition

`PASS_GEOMETRY_MAP_BARRIER_CONSTRUCTION_ONLY`. Before the main loop, the Entry was unmapped with width/height 1 and root coordinates (0,0). The observed Configure and Map event times both preceded the accepted sample. Afterwards it was mapped at (143,82), size 294x23, within a mapped 420x180 root at (80,70); app exit was 0. The requested Tk geometry and realized Entry geometry differ as expected because of widget layout/decorations; the audit checks the actual widget rectangle.

## Limits / evidence-quality note

This supports only the local geometry/map sequencing discriminator. It does not test focus, key delivery, first-character loss, fixed-delay readiness, load effects, or task correctness. Raw JSON does not embed its own source hash or main pin; those identities are in the pre-run freeze and the recorded pre-run hash readback, so downstream consumers must pair the raw with this manifest. No corruption-mutation suite was run for this small auditor. The result is therefore a bounded construction PASS, not qualification of the complete Issue #5260 successor or runtime integration.

The original #5260 r0 STOP remains untouched. No Docker, GUI input, XTest, model/provider, GPU, or user display was used. No Xvfb process remained after the invocation.
