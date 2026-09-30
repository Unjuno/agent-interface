# Issue #5273 — T0 v3 successor result

**Disposition: PASS_HOST_CONSTRUCTION_ONLY; container formal STOP_NO_EXPLICIT_RESOURCE_LEASE (zero invocations).** The independent audit verifies all eleven plans, including the multi-check aggregate behavior. This is not formal/container evidence or runtime-routing qualification.

## H/T/D/C/U

- **H:** A versioned authority-neutral registry can classify every check in an actual #5268 IR plan before dispatch, preserving unavailable state and estimate provenance.
- **T:** Ten one-check boundary plans and one two-check dependency-bearing plan; independent literal raw auditor; exact row/schema/identity checks.
- **D:** Exact per-check and aggregate outcomes, one-to-one assignments/decisions, independently valid IR shape, zero dispatch, no authority, and source/input/raw digests. Host PASS is distinct from container formal PASS.
- **C:** Descriptors/costs may be stale or false; fixed synthetic cases do not establish distributional or backend behavior.
- **U:** No verifier correctness, measured latency, scheduling benefit, runtime integration, or authority. Deadline milliseconds are fixture-only interpretation.

The initial exact-output-schema mismatch is preserved under `CONSTRUCTION_FAILURE_01.json`; it was corrected before freeze. The independent auditor is not included in the pre-run source freeze to avoid a circular hash dependency; its source SHA is recorded in the resulting audit and its exact blob is retained in the commit. The freeze hashes candidate, fixture builder, test oracle, registry, tests, plan and runner; the imported #5268 candidate is separately SHA-bound. The raw-only audit independently checks fixture IR shape and exact raw/plan/decision schemas and identities.

## Execution and hashes

- Base: `4e2c0cf6241e3068bbc1afde8c97206c6b731a1b`; branch `research/verifier-registry-5273-t0-v3-20260930`.
- Host: Python 3.14.5, macOS arm64. Construction tests: **5/5 passed**.
- One frozen host construction execution: **11/11 plans** matched exact per-check and aggregate literal outcomes; zero dispatches.
- Freeze SHA-256: `2ca6eaff9bc44c64303c798c463f11fec4e591b2a18033d260035e2994c8abe4`.
- Raw SHA-256: `3a7db8296e6447279ae0907899206d5e19c1769a66f097bad1c624ac82d9eb4c`.
- Raw-only audit SHA-256: `5aa7f44fc5c76ebe979cab8f1afc714750788016425ae5db90b8f1bf816f5fed`; auditor source SHA-256 `3d29f5ea7280303908781c693821270efb50817053f0906afaea8db3a14c3f00`. Source/input bindings true, errors zero.
- Container disposition: **STOP_NO_EXPLICIT_RESOURCE_LEASE**; invocation count 0. No Docker/OrbStack command was run.
