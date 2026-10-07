# Independent blind review B — evidence/control-first

Reviewer: isolated sub-agent B; received only the frozen profile/evidence packet; did not receive candidate outputs.

| Case | Mandatory controls and evidence grade | WSLc | Native WSL | Ordinary Linux process container / Docker | Separately managed VM | Unknown runtime |
|---|---|---|---|---|---|---|
| 1. Trusted pinned read-only CPU replay | Pinned image and read-only input required. Historical smoke observed command completion with --pull never and Windows-host read-only bind rejecting a write (EROFS); scoped historical evidence, not current readiness. | HOLD — scoped evidence exists, current readiness/ownership unknown. | ELIGIBLE_SCOPED for stated trusted workload if available and its replay controls demonstrated. | HOLD — Docker CLI not discoverable; current readiness unknown. | HOLD — availability/health unproven. | HOLD — identity/controls unknown. |
| 2. Arbitrary untrusted code; protect Windows files/credentials and peer workloads | Malicious-code containment mandatory. Microsoft WSL model rules out WSL as a security sandbox from host/user; NIST notes shared-kernel containers are not robust hostile multi-tenant boundary absent additional VM. No evidence a dedicated VM is available. | INELIGIBLE — WSL boundary mismatch. | INELIGIBLE — same WSL mismatch. | INELIGIBLE — ordinary process container does not meet stated boundary on this evidence. | HOLD — candidate route in principle, but existence/availability/containment unproven. | HOLD — identity/boundary unknown. |
| 3. Trusted CPU work; effective memory ceiling <=128 MiB | Effective hard ceiling mandatory. Direct counterevidence: 128 MiB arm retained 384 MiB; policy says accepted --memory did not prevent that. | INELIGIBLE — documented mismatch. | HOLD — no effective ceiling evidence. | HOLD — requested 256 MiB does not demonstrate enforcement. | HOLD — no evidence. | HOLD — unknown. |
| 4. Trusted integration requiring Compose/Engine API | Frozen Compose/Engine API required. | INELIGIBLE — WSLc has no Docker-compatible socket. | HOLD — no evidence. | HOLD — appropriate runtime class in principle, but Docker CLI unavailable in attached environment/current readiness unproven. | HOLD — no evidence. | HOLD — unknown. |
| 5. Trusted code; independently demonstrated outbound denial | Effective denial independently demonstrated; --network none is configuration only; no probe retained. | HOLD — required denial not independently demonstrated; readiness unknown. | HOLD — no evidence. | HOLD — no evidence. | HOLD — no evidence. | HOLD — unknown. |
| 6. Trusted replay; read-only source and separate output | Source bind demonstrably rejects writes; output separate. Historical EROFS is scoped evidence; separate output absent from packet. | HOLD — source-write control historical, but separate output/current readiness unproven. | HOLD — both controls unproven. | HOLD — both controls unproven. | HOLD — both controls/availability unproven. | HOLD — unknown. |
| 7. Isolation-required workload with runtime/owner unknown | Runtime identity/configuration/owner mandatory. | HOLD — #7924 says WSLc ownership unknown and prohibits further management/RPC pending gate. | HOLD — unknown. | HOLD — current Docker availability/configuration unknown. | HOLD — VM identity/owner unknown. | HOLD — unknown. |

Mutations:
- M1: removing EROFS leaves case 6 HOLD; no route may claim rejection from configuration alone.
- M2: reject effective-cap claim; WSLc remains INELIGIBLE for case 3 because #6355 is direct counterevidence and policy disclaims the guarantee.
- M3: missing threat-model premise requires HOLD pending assumption/boundary evidence; default routing cannot supply it.

Unsupported/missing claims: current WSLc readiness/ownership, Docker runtime readiness, available healthy VM, independent network blocking, separate output for case 6, malicious-code containment, broad parity/performance/security.

Assessment: route names/defaults miss threat boundary, memory enforcement, protocol compatibility, and observed behavior. Alternative recommendations do not establish availability.