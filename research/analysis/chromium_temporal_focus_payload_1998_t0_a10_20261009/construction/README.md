# Construction checks

All checks use a generated 5×4 RGB PNG only. The fixture has rows encoded with PNG filters 0 through 4; the candidate container parses it, writes a 3×2 crop, and a separate Python implementation verifies exact pixels and the raw auditor's six mutation controls. The size-saving assertion is intentionally absent from construction checks because a tiny synthetic image can have negative payload savings after metadata.

- `attempt-01/` records the initial incorrect assertion that even the tiny fixture must save bytes.
- `attempt-02/` records the candidate codec pass before the independent auditor harness was added.
- `attempt-03/` records the candidate and independent auditor/mutation pass before disabling Python bytecode output in the harness.
- `attempt-04/` records the same pass using the final construction-test source that is included in the freeze.

These are construction outputs, not formal allocation results. The formal candidate has not run yet.
