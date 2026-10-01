# One-shot audit successor v3 — 2026-09-28

Allocation 01 stopped before audit due to native module loading with default tmpfs execution flags. Allocation 02 stopped before audit due to nested shell quoting. Preserve both STOP records; do not retry those IDs.

## H/T/D/C/U

- **H:** The exact W2 schema/cases identified in PLAN.md pass the official Draft 2020-12 meta-schema and instance checks, while fixed malformed schema/data controls are rejected.
- **T:** Run one frozen Python launcher directly as Docker's command (no `sh -c`) using launcher SHA-256 0f2b7510c3fb4298da045ca3adc213f136a8aa5fccc7dd3d2c5d4e6c6e613150; candidate auditor SHA-256 ca3b0a627faf6a3878af5eeaf85c01f6640a11d65413156008578d7649372ac0; independent auditor SHA-256 ec4f0701668e7c98ea649192ee5fa78fccb4e755660d491712b6c4456493057f. First run a distinct disposable dependency-loader preflight only (imports jsonschema and rpds, no schema audit); then execute the candidate once into a new results-v3 directory. Keep the independent audit for a separate subsequent read-only container invocation. Use exact main snapshot, Git blobs, image and wheel hashes in PLAN.md.
- **D:** Same frozen acceptance: valid schema, 8/8 examples, 7/7 invalid schema mutants rejected, 7/7 invalid instance mutants rejected, and source hashes exactly match. Otherwise retain outcome, no retry.
- **C:** JSON Schema standards conformance for the frozen synthetic examples only. No semantic cross-event, live input/effect, or runtime claims.
- **U:** No clock calibration, physical occupancy, task utility, recovery efficacy, Worker return, lease inventory, or Gate-1 completion. Does not authorize W3/W4/formal work.
