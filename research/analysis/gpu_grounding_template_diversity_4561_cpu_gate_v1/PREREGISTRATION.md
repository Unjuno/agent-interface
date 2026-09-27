# CPU construction gate preregistration

Allocation: `gpu-grounding-template-diversity-4546-successor-01-cpu-gate`.

This is a supplemental STOP-boundary check for Issue #4561. It is independent
of the frozen three-seed CNN allocation and cannot reopen it. The canonical
formal GPU allocation remains `STOP_CUDA_DETERMINISTIC_ADAPTIVE_POOL_BACKWARD`
with zero optimizer steps; no CUDA operator or optimizer is invoked here.

## Frozen sources and data

- Renderer and geometry specifications: `render_audit.py`, SHA recorded in
  `SOURCE_SHA256SUMS.txt` before execution.
- Independent auditor: `audit_cpu_gate.py`, same source freeze.
- Twelve unique families are generated from integer geometry constants in
  `specs()`; family IDs 01–08 are train, 09–12 held out, split before the four
  content/theme variants per family.
- Every image is a locally drawn 1280x800 RGB PNG. Field and submit labels are
  exact centers from the fixed family geometry. No external images or fonts.
- Formal GPU data/metrics are not generated, consumed, or inferred.

## Decision

Pass only if 12-family/48-image cardinality, 8/4 family split, unique RGB
hashes, deterministic repeat-render pixels, exact geometry labels, source PNG
hashes, strict contract validation, 32px-center geometry, and corruption
rejection all pass. Otherwise record gate FAIL. Outcome scope is strictly
renderer/label integrity; no hypothesis or model result.

## Exact command

`python render_audit.py` followed by
`python audit_cpu_gate.py <output-directory>`.
