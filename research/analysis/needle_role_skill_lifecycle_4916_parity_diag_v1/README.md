# Role-skill scorer parity diagnosis (Issue #5053 successor)

This additive allocation diagnoses the role-B construction failure retained on
Issue #5053 and in first-rung allocation `...-01`. The old source and result
remain unchanged. The suspected defect is the LoRA output matrix orientation:
the retained loader computes `h @ a @ b` with `a: 16x2`, `b: 2x4`, while the
first-rung scorer passed `b` directly to a row-major `linear` helper that
expects `4x2`.

The experiment transposes B only for scoring, then compares the corrected
implementation against all 12,288 retained loader predictions. This is a
construction/parity diagnostic, not lifecycle timing evidence. Formal timing
may proceed only in a separately frozen allocation after exact parity passes.
