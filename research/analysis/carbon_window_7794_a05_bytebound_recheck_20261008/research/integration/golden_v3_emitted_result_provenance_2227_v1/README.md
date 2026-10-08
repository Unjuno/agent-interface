# Golden v3 emitted-result provenance (#2227)

Source-first additive audit. No model, GUI, network, input, Docker, or runtime execution.

## Frozen sources

- `runtime/golden-demo-v3.sh`: `ef489bbd68e3f80fac060b179fe90da2cce8d209`
- `runtime/golden_desktop_demo_v3.py`: `26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2`
- `runtime/golden_desktop_demo_v2.py`: `cf777186879fc3d550194aa9cbc8a7239ca991ff`

## Initial source finding

v3 delegates `run_live` to v2 and v2 constructs a report dictionary with a machine-readable `schema`, `passed`, usage, routes, task rows, release checks, independent evaluation, and environment fields before writing `golden-report.json`. This is stronger than report prose alone, but it does not by itself prove that every proposed golden-v3 lifecycle field is emitted or that task success/partial effects map to the CLI schema.

Disposition remains `HOLD_FIELD_PROVENANCE_INCOMPLETE` pending exact v2/base runner and retained artifact field tracing.

Counters: model=0, GUI=0, network=0, input=0, Docker=0, formal=0.
