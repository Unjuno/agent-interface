# Issue #4649 — auditor-v3 resolved-path confinement controls

## H / T / D / C / U

- **H:** Resolving each input path and requiring the resolved target to remain beneath the canonical input root will reject out-of-root symlink escapes while preserving ordinary files and in-root symlinks.
- **T:** One new controls-only Docker allocation over five synthetic cases using an additive v3 wrapper derived from the exact #4672 v2 source. A v1 PASS stub isolates ledger/path behavior. Cases: regular in-root file, in-root symlink, literal `../` traversal, input symlink to a sibling outside file, and the manifest itself symlinked outside. Do not invoke the formal runner or prior eight-control harness.
- **D:** Scoped PASS iff both in-root cases return `PASS_INDEPENDENT`; the three escape cases return structured FAIL with the expected V3 error and empty stderr; all source/image identities match; no exception or retry. Any escape accepted is `FAIL_PATH_CONFINEMENT`; an in-root false refusal is `FAIL_COMPATIBILITY`; source/environment mismatch is STOP.
- **C:** Local Docker Desktop; cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14, Docker 28.5.1. Network none, pull never, read-only root/source, one CPU, 256 MiB, 32 PIDs, 32 MiB noexec/nosuid tmpfs, dedicated output. The v2 base source SHA is `500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630`.
- **U:** Synthetic unit-level ledger checker only, with v1 stubbed. This is a candidate fix characterization, not a formal01 rerun, not validation of v1 or #4672's eight controls, and not production/file-system race testing. `Path.resolve` containment relies on the supplied read-only input tree remaining stable during this bounded audit.

Allocation: `issue4649-auditor-v3-path-confinement-20260927-01`.
