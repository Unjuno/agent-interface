# WSLc private-session portability smoke — 2026-10-05

## H / T / D / C / U (frozen before invocation)

**H.** A uniquely named temporary WSLc session can run one cached, network-disabled, read-only-bind CPU container without relying on or enumerating the default/shared session. This is a narrow isolation/portability check, not a Docker parity or performance hypothesis.

**T.** Use WSLc 3.0.1 on Windows with a fresh GUID session name and fresh temporary session-storage path. Keep that session alive in an owned terminal. In a separate caller, invoke one container by the exact pinned cached Python image digest with `--pull never`, `--network none`, `--cpus 0.25`, `--memory 256M`, a uniquely named container, and one unique host sentinel bind-mounted `:ro`. The Python process must verify sentinel bytes and prove a write fails with `EROFS`. Then inspect only that exact container name in that exact session and confirm it is absent after `--rm`. Do not issue any default-session operation or global container inventory. Terminate only the uniquely named session by closing its owned shell. Bound every operation to 30 seconds; retain first outcome, including infrastructure STOP/HOLD, without retry.

**D.** `PASS_PORTABILITY_SCOPED` only if session creation, one run, exact sentinel read, rejected write, exit 0, exact-image identity, and targeted absence inspection all complete within 30 seconds; record host cgroup/swap caveat. Any timeout, missing cached image, invalid session, unverified identity/cleanup, or output mismatch is a retained `HOLD`/`STOP`, not a positive container result. Candidate invocation budget: exactly one; no rerun.

**C.** The experimental session may share host WSL VM CPU, physical memory, kernel, storage, and service internals with other users; a session name is not proof of resource isolation. WSLc may differ from Docker in untested behavior. Cgroup/swap limits may be unavailable. The pinned image may not be cached in the private session and pulls are forbidden.

**U.** One local host, one Python image and one short CPU smoke only. No Docker comparison, speedup, memory relief, OOM prevention, broad Docker parity, CI workflow migration, GUI/runtime, or application-quality claim.

## Frozen identities and boundary

- Base `main`: `0db00a564daff64e47fd6931954ace0f71ab8f2b`.
- Local branch: `migration/wslc-isolated-session-smoke-20261005`.
- Runtime target: Microsoft WSL `3.0.1.0`, WSLc `3.0.1.0`; Ubuntu is WSL2 (not a WSL 3 distro).
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64), only with pull policy `never`.
- Candidate bytes: literal UTF-8 `wslc-private-session-readonly-probe-v1`.
- Preflight read-only Windows process query observed zero `wslc.exe` clients; C: had 9,127,612,416 bytes free. This is a point-in-time observation, not peer release confirmation. Use only a named temporary session and session-scoped commands; do not inventory, operate on, or clean the default session.
- `wslc` top-level, `run`, `system session`, `system session enter/run/terminate`, and `container inspect` help were read. `session enter <storage-path> --name <name>` creates a nonpersistent session removed when its shell exits; `--session` scopes later commands. No session/container operation has yet been invoked.

No Docker command, WSL shutdown, default session operation, pull, build, prune, shared cleanup, or memory pressure is authorized by this smoke.
