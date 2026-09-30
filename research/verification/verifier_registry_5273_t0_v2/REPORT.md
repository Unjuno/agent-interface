# Issue #5273 — T0 v2 successor result

**Disposition: PASS_HOST_CONSTRUCTION_ONLY; container formal STOP_NO_EXPLICIT_RESOURCE_LEASE (zero invocations).** Ten schema-valid #5268 IR plans matched a literal raw-only audit. This is still a host construction result, not formal/container or runtime-routing qualification.

## Review-driven changes

Independent review of v1 found the auditor shared its imported oracle, weak row-identity/binding checks, and precedence that could classify a hard incompatibility as unavailable. V1 remains unchanged. This separate version embeds literal expected status/reason/cost tuples in the auditor, checks exact case/check bijection and raw schema/allocation/base/input digests, gives hard incompatibilities precedence, includes output-role and unknown-verifier cases, and validates real #5268 IR v0.1 documents with its frozen validator.

The pre-freeze `CURRENT_INTENT` fixture/oracle mismatch is preserved in `CONSTRUCTION_FAILURE_01.json`; corrected case is `CURRENT_PERMISSION`, which is a valid role enum but unsupported for this descriptor. A pre-freeze missing-`freeze.py` command failure is preserved in `CONSTRUCTION_FAILURE_02.json`; no run/allocation was consumed by that setup error.

## H/T/D/C/U

- **H:** A versioned authority-neutral registry can classify valid IR plans pre-dispatch, distinguishing incompatibility from temporary unavailability and retaining estimate provenance.
- **T:** Ten schema-valid IR plans; literal auditor map separate from the candidate; exact rows, roles, costs, zero dispatch, and identity/hash gates.
- **D:** PASS only for exact one-to-one case/check IDs and expected statuses/reasons/cost estimates, `authority=none`, zero dispatch, frozen source/input identities, and successful mutation controls. Host PASS is not container formal PASS.
- **C:** Registry capability declarations may be false or stale; estimates may not match target hardware; finite fixtures may omit interactions.
- **U:** No real backend call/correctness, measured SLA, scheduling/speed benefit, runtime integration, cross-host qualification, or action authority. The numeric #5268 deadline unit is assumed as milliseconds only within these fixtures.

## Execution and hashes

- Base: `c12e6079f82d1604a9f9a08445a314e4d59d8846`; branch: `research/verifier-registry-5273-t0-v2-20260930`.
- Host: Python 3.14.5, macOS arm64. Construction suite: **7/7 passed**.
- Frozen host execution: **10/10** statuses/reasons/cost estimates matched; zero dispatches.
- Trusted freeze SHA-256: `8be490ec36eed7ceccf4c3884bd0129ab337f0c873616f35e9dfe14edf920347`.
- Raw SHA-256: `aa53e2a02ed204da433389a375d9582be72e6a8be30f80966105f169aafa8b7a`.
- Raw-only audit SHA-256: `1fa93e25c37903acda90e10a075ac7e5590cb00496c8478571b3fe5fba8eb188`; source and input bindings true, errors zero.
- Container: **STOP_NO_EXPLICIT_RESOURCE_LEASE**, invocation count 0. No Docker/OrbStack command was run. The formal container result remains unobserved.
