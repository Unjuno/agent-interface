# Post-hoc classification supplement

This supplement classifies the single preserved construction row independently of the runner's literal outcome tags. It does not change or replace the original raw row, frozen audit, or `STOP_CONSTRUCTION` disposition.

## Result

- Harness completion: `COMPLETED` (the harness completed its UNO edit sequence; this is not an Agent Interface runtime terminal).
- Live-view predicate: `MATCH` (A1 was 7.0 in the in-memory document).
- Saved effect: `CONTRADICTED` (independent disk reopen found A1=0.0 and the source SHA-256 remained stable).
- Frozen construction gate: `STOP_CONSTRUCTION`, because the audit's visible-window selector detected no Calc window.

The post-hoc classifier and four standard-library unit tests ran in the pinned LibreOffice 7.4.7.2 container. All four tests passed. The full classification was emitted from the retained raw/audit JSON in a separate additive output. This remains a one-case construction pilot, not formal allocation, public runtime execution, or model-facing policy validation.

## Reproduction

Run `python3 -m unittest discover -s . -p 'test_*.py' -v` from `posthoc_v1/` and invoke `run_classification.py --raw <raw.json> --audit <audit.json> --out <new-output-path>`. The container should be pinned to `issue-2849-task1-runtime:v3-20260921` (linux/arm64, image digest recorded in `RESULT.md`). Inputs are read-only; choose a new output path because the CLI refuses overwrite.

### Executable checkout command (review correction)

The initial `posthoc_v1/` reference above predates publication of its CLI and is superseded. The additive runnable entry point and adjacent classifier are in `posthoc_v3/`. From the repository root, use a fresh output directory:

```sh
OUT_DIR="$(mktemp -d)"
python3 research/integration/calc_effect_contract_34_pilot_v1/posthoc_v3/run_classification.py \
  --raw research/integration/calc_effect_contract_34_pilot_v1/results/calc-effect-contract-34-pilot-20260927-01/raw.json \
  --audit research/integration/calc_effect_contract_34_pilot_v1/results/calc-effect-contract-34-pilot-20260927-01/audit.json \
  --out "$OUT_DIR/classification.json"
```

This is a posthoc JSON classifier only; it does not launch Calc or represent a fresh experiment. Its output is written outside the tracked, occupied `results/` tree.
