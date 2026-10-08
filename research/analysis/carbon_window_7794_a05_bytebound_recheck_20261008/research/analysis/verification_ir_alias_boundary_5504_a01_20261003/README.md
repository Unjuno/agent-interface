# Verification IR alias boundary — #5504 A01

Prospective finite analytical allocation: #5504 comment 5968198522, implementing
the method follow-up in comment 5937946951. See SCHEMA.md and PROOF.md.
This is not the production IR, a runtime/portability test, or a consumed rerun.

The package separates a projection-based producer, independently authored
raw-byte auditor, construction tests/corruptions, and one frozen formal
allocation. Formal outputs and first failures are records, not rerun recipes.
After source freeze, do not repair/re-execute this allocation. New formal
questions need an independently scoped successor, not a wrapper-only rerun.

Safe integration checks (no formal modelchecker/auditor allocation):

```powershell
python -B -m unittest -v test_modelchecker test_audit test_capture
```

These operate on pure/independently constructed fixtures only, including short
owned child processes for capture/timeout/interrupt tests. They neither launch
containers nor read or overwrite formal results. They are not a full
repository suite or production safety test. REPORT.md records actual outcomes.

WSLc remains the user's selected container route without Docker Desktop, but
the shared #5085 HOLD is not lifted by this artifact. WSLc/Docker/model/GPU/GUI
formal counts in A01 are zero; this exact finite question needs no container.
No engine/VM/settings/process/memory-allocation changes are made in A01.
