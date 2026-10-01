# Role-skill lifecycle amortization — corrected first rung

Successor on Issue #5053 after immutable first-rung -01 construction STOP and
parity diagnostic `needle-role-skill-lifecycle-4916-parity-diag-20260928-01`.
The corrected candidate transposes stored LoRA B (2x4) for the row-major
output-by-input scorer. The parity diagnostic independently verified all
12,288 retained seed-3788 predictions before this lifecycle allocation.

This allocation runs that corrected candidate through the original first-rung
question: five paired AB/BA blocks, 40 deterministic requests per arm per
block, with loading/validation/construction included in each arm's lifetime.
Reuse setup is included in its cost. It is limited to this package, seed, image
and first-rung sample; it is not the former 1,000-request gate or a product
performance claim.

Construction, formal, and independent audit are distinct one-shot invocations.
Any failed source/input/image identity, parity check, process, or audit is
retained without retry; formal does not run unless construction passes.
