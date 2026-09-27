# CUDA extent-readout result

This directory contains the frozen #4850 CUDA construction run and a separately versioned posthoc audit. The posthoc work does not repeat or modify the GPU fits.

- `REPORT.md`: H/T/D/C/U and scientific STOP result.
- `src/`: immutable run sources plus deterministic input regenerator and v2 CPU auditor / mutation controls.
- `out/result/`: retained raw, weights, original audit and controls, plus v2 audit and regeneration receipt.
- The original `AUDIT.json` and 5/8 `CONTROL_RESULTS.json` remain unchanged; v2 outcomes are distinct files.

