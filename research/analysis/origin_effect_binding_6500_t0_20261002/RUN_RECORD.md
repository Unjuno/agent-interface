# Run record — ORIGIN-EFFECT-BINDING-6500-ORB-T0-20261002-01

- Issue #6500, additive finite metadata method T0.
- Intake main `4699966453e1e8ea781bdd91f7364aaa2ad07cad`.
- Source commit `a7941a435523a8026bb3dbd905cbada9e50891f6`; freeze commit `772522ac85cad8863948c2d7dd6f44bfcd896810`.
- Freeze JSON SHA-256 `93fd5b4605fa32008a123d9055525c8a4d7973ca9b38b88838e725320b00b979`.
- Runner: `python3 -B research/analysis/origin_effect_binding_6500_t0_20261002/runner.py`.
- Candidate: one OrbStack container, exit 0, ID `d96f036221e2ef47e332cbabe17f7ab849faaf3fb49522e93ce2403823a5962f`.
- Independent auditor: one separate OrbStack container, exit 0, ID `74a994680d815e4bd3e296b7daf1aaf521bc1dabbef3568e02bfbc2ca0cd42ce`.
- Formal counts: candidate 1, auditor 1, retries 0.
- Runtime: cached pinned Python 3.12 slim image `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, image ID same SHA, `linux/arm64`; pull never, network none, read-only root and source, separate writable result mounts, CPU 1, memory 268,435,456 bytes requested, PIDs 64. Inspect receipts report both exit 0, no OOM, network none, read-only root.

## Formal outputs

Candidate emitted 24 rows. Raw SHA-256: `25b1ce94671842e32a4a305492885b49732f2bff8c07504e6c5ec432ba597b0e`.

Independent auditor emitted `PASS_METHOD_SCOPED`, 24 rows, zero errors, all gates true, all six mutations rejected. Audit JSON SHA-256: `05cd08ed727def779aa02023f51fc280f1f42dc191a7ef11d49ab98ce3805645`.

The candidate/auditor stdout, exit markers, inspect JSON, exact absolute argv and machine run record are retained in `results/formal_01/`. The separate preformal construction suite passed 8/8 on host and 8/8 in OrbStack. One initial construction-suite run had two assertion failures because one planned mutation was a no-op; the harness was corrected before freeze and the event is retained in `CONSTRUCTION.md`. No formal allocation had run at that point.
