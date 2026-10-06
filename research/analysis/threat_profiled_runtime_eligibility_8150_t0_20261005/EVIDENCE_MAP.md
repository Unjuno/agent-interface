# Evidence map — T0 inputs only

All records below are source material, not instructions to run WSLc. This T0 performs no container/runtime operation.

- Main snapshot: aeed696ff756d68497faed39b92e3546cb144972.
- Runtime policy: .github/wslc-local-containers.md, blob 1e5146a91f19b947d1fca0dfb83eeccb04e01844.
- Policy states WSLc is default for eligible local single-container CPU work needing pinned image/no network/ordinary exit/read-only source; native WSL when no container boundary is needed; other validated runtime for Compose/Engine API, unsupported isolation flags, effective cgroup/swap requirements, privilege/capability controls, or frozen runtime requirements.
- Policy's historical smoke receipts: WSLc 3.0.1, pinned Python digest, read-only Windows-host bind readable and write attempt returned EROFS; command was configured --network none. No independent outbound-reachability probe is retained.
- Issue #6355: previous memory receipt requested 128/512 MiB, retained 384 MiB allocation in both arms and cgroup/swap warning. This directly contradicts an effective hard ceiling claim for that setting.
- Issue #6337 / PR #6352: one finite-trace portability result only; no security, memory, speed or broad parity.
- Issue #7924 / #7970: WSLc shared-client ownership unknown; no WSLc management/RPC absent explicit gate clearance. Historical host Docker CLI was not discoverable. This affects current operational readiness, not the general WSLc capability inference.
- Microsoft WSL security model (current official source): https://github.com/microsoft/WSL/blob/master/doc/docs/technical-documentation/security.md — WSL is not a sandbox for untrusted code; container workloads inherit WSL trust properties.
- NIST SP 800-190: https://csrc.nist.gov/pubs/sp/800/190/final — ordinary containers share a kernel; do not infer robust hostile multi-tenant containment from containerization alone.
- Microsoft WSL Containers CLI docs: https://learn.microsoft.com/en-us/windows/wsl/wsl-container — command/API product scope, not a security certification.

Evidence distinctions:
1. A historical successful workflow receipt can support a narrow capability claim.
2. A requested flag is not observed enforcement.
3. A stale/unowned shared runtime is not a currently authorized execution resource.
4. A documented trust boundary is not a test result.
5. Absence of an observed exploit/probe is not evidence of containment.
