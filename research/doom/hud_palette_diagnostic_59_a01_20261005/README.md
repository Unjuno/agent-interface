# Saved HUD palette diagnosis A01

[Result and limits](REPORT.md), [prospective protocol](PROTOCOL.md), [input/source hashes](FREEZE.json), [retained first output](run-01/result.json), [invocation](invocation.json).

[Independent saved-pixel audit](audit-result.json) and its [separate decoder/scorer](audit_saved.py) reconstruct all56 projections and pass144/144 checks. Example saved-only audit command (use a new output name): `python -B research/doom/hud_palette_diagnostic_59_a01_20261005/audit_saved.py --wad <hash-bound-freedoom2.wad> --output <new-audit-output.json>`.

This package records new analysis of two retained PNGs from `research/doom/v16_comparison_unknown_59_4d74_20261004/`, already preserved in main. Use the paths and hashes in `FREEZE.json`; the full 28,787,748-byte WAD is an external hash-bound dependency, not a missing newly generated result.

`probe.py` is guarded by an explicit main entry point and has no runtime import integration or test-discovery name. It reads local saved files and refuses a preexisting output directory. Do not replay the consumed A01 diagnostic or the original live arms as validation; use the independent saved-data audit. An explicitly authorized future reproduction must use a new, declared output and retain its own provenance.
