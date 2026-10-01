# Issue #5537 T9 — nested admission records and mutation adequacy gate

## H / T / D / C / U

**H.** An explicit typed policy boundary can preserve useful `APPROXIMATE_SECTION` evidence while refusing irreversible admission by default. The experiment is only auditable if decision inputs and solver outputs are separate nested objects, and every corruption control is proven non-identity before audit.

**T.** Against fresh main, freeze one finite 135-row matrix: five bundles (exact, within tolerance, beyond tolerance, no global sections, missing context), three tolerances, three contracts, and three action classes. Candidate enumerates all eight assignments and emits `{decision_input: ..., decision_output: ...}` without flattening/merging. Independent raw-only auditor intersects relation bitmasks and reconstructs output. Six mutations target nested output admission, status, nested input tolerance, nested fixture declared spread, omitted row, and duplicated row. A mutation manifest asserts selector uniqueness plus exact before/after values; unit tests exercise all mutation preconditions before formal freeze. One candidate and one separate auditor invocation only; no GUI/model/network/external effect.

**D.** PASS scoped iff 135/135 base rows equal the independently reconstructed values; exact sections admit; within-tolerance approximate admits reversible/compensable by default and refuses irreversible by default; explicit approximate-irreversible contract opts in only for that class; beyond-tolerance/no-section/missing-context never admits; all six controls are proven non-identity and rejected. Any unsafe admission is FAIL; any raw/base mismatch or nonfunctional mutation is STOP.

**C.** Synthetic binary assignments and hand-authored scalar tolerance; policy contracts are model assumptions, not authenticated runtime contracts.

**U.** No general sheaf algorithm, calibrated interface tolerances, live evidence, GUI, model, task-effect, empirical safety, or production claim. T5–T8 STOP records remain immutable and are not input rows.

## Freeze protocol

- Freeze base main: `94dbdc8a04a78eb5dc6089058e74b7cec31bbdc4`.
- Allocation: `gluing-approx-irreversible-5537-t9-20261001-01`.
- New additive path: `research/analysis/gluing_approx_irreversible_5537_t9_v1/`.
- CPython 3.14.5/macOS arm64 host-local; no exact container lease, so no Docker inspection/use.
- Construction test once before freeze; one `python3 -B run_experiment.py`; if exit 0, one `python3 -B audit_raw.py`; no retries/post-freeze edits.
