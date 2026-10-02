# OrbStack audit-only allocation 04 — Issue #6350

Status at freeze: `PREREGISTERED_NOT_RUN`.

## Why this allocation exists

Allocation 03 remains immutable with construction=1, candidate=1, auditor=1, retries=0 and terminal `STOP_METHOD_FAILURE`: its only auditor container had no writable `/out` mount and exited before writing/printing an audit receipt. Do not rerun that allocation or candidate. This is a fresh audit-only allocation against the exact retained candidate output, with no candidate invocation.

## H / T / D / C / U

**H:** The frozen independent raw-only auditor can reconstruct the retained candidate result from the exact fixture, produce its audit JSON when the output mount is present, verify 10 task/30 display records, and reject all four preregistered semantic mutations.

**T:** Allocation `EFFECT-TERMINAL-FEEDBACK-6301-RAW-AUDIT-ORB-20261002-04`. Frozen main `9a573b00dc595e64d09387e567c85e10b61a46c1`; it must remain an ancestor of the branch and freshly fetched main. Exact fixture SHA-256 `35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9`; auditor source SHA-256 `831ad1e7a499b1d28bd5b0b9fbfb10b9f5409eddc47460e4a28209d84055977e`; retained T03 candidate raw SHA-256 `c6024886ab276f24a033c18c5446651eae3adb30bb58ed3c999c1b77595085e1`. Candidate invocations for allocation 04=0; raw-only auditor=1 maximum; retries=0. The T03 raw input is mounted read-only at `/in`; source/fixture is read-only at `/src`; a fresh separate `/out` bind is writable. The output path must be absent before the run.

Runtime: dedicated OrbStack VM `effect-terminal-feedback-6301-t0-orbstack-20261002`, Docker 29.1.3, image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (Python 3.12.14 ARM64), no pull, network none, read-only rootfs, all caps dropped, no-new-privileges, UID/GID 65534, requested 0.25 CPU / 512 MiB / 64 PIDs. Retain Docker inspect and in-container cgroup values. This adjudicates one synthetic candidate output only; no GUI/model/game/GPU/input.

**D:** `PASS_AUDIT_ONLY_SCOPED` only when the one audit process exits 0, reports `PASS_METHOD_SCOPED`, reconstructs 10 tasks and 30 display records, and rejects all four mutations. A mismatch is FAIL; runtime, mount, provenance, or receipt failure is STOP. No retry.

**C:** One deterministic finite truth table and one retained candidate output. The extra allocation exists solely because T03's report destination mount was omitted; it does not repeat candidate work or alter T03.

**U:** No model behavior, GUI/application effect, human benefit, safety rate, efficiency, latency, MAP01 result, or broad generalization.

## Exact command

`run_audit_orbstack_04.sh` verifies source/input hashes and main ancestry, refuses existing output/marker, starts one named container, saves stdout/exit/container inspection, and never invokes a candidate.
