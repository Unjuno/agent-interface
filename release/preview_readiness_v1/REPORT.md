# Research Preview release-readiness audit v1

Status: **PARTIAL PASS — launcher fixed; supported-host setup/doctor and fresh golden run remain open.**

Base: `aa4be696dbf9096acd2e9b55576d965cbdf98cbf`.

This is an independent release-side audit performed after the scoped launcher-permission repair. It does not modify runtime semantics, research allocations, benchmark data, or launch claims.

## Executed checks

### 1. POSIX launcher boundary — PASS

PR #92 changed only the Git modes of:

- `runtime/setup-golden-demo-v3.sh`
- `runtime/golden-demo-v3.sh`

from `100644` to `100755`; current-main comparison showed zero content additions/deletions for both paths. A fresh disposable Linux container independently reproduced direct execution exit `126` for both scripts at mode `0644`, then successful fail-closed dispatch after mode `0755` using the same launcher logic. The repair was merged as `aa4be696`.

This proves only the direct-exec permission boundary. It does not prove package installation or GUI/model readiness.

### 2. Offline Actions lab artifact integrity — PASS at its declared scope

Artifact `10398313098` from packaging-only workflow run `34973453255` was downloaded through GitHub MCP. Observed archive:

- name: `offline-container-lab-9e6d5ecd`
- bytes: `80,117,931`
- SHA-256: `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`
- ZIP entries: 14
- source base in manifest: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`
- included wheel count: 12

The artifact is useful for offline research/container experiments. It is **not** a user-facing runtime preview artifact.

### 3. `audit-retained` from the offline lab source bundle — FAIL, retained

Running:

```bash
python3 runtime/golden_desktop_demo_v3.py audit-retained
```

against the extracted offline source bundle returned exit `2` with:

```text
FileNotFoundError: research/live_control/results/integrated-efficiency-live-01/preregistration.json
```

The missing path is referenced by the runtime retained-audit implementation. GitHub repository search confirms the audit/preregistration source expects that retained result directory. Therefore the offline lab source bundle must **not** be presented as the runtime-preview distribution or as evidence that the golden retained benchmark is self-contained.

This does not demonstrate that a normal full GitHub checkout fails; it demonstrates only that this particular offline research bundle omits files required by `audit-retained`.

### 4. Supported-host contract — documented but not newly executed

`runtime/README.md` states that the promoted demo runs under Linux/X11 with **WSLg as the current tested host**, and that the model bridge uses the Windows Codex installation from WSL. `doctor` additionally checks display, X11 connection, Chromium, and the Codex CLI bridge.

The generic Linux container used for this audit is therefore not a valid substitute for the supported-host acceptance run. No claim is made that the current pinned Python dependencies work on arbitrary Python 3.13 Linux hosts.

## Launch gate disposition

| Gate | Status | Evidence / action |
|---|---|---|
| Direct documented launcher invocation | PASS | mode-only repair merged at `aa4be696` and independently reproduced |
| Downloadable runtime artifact | UNKNOWN / OPEN | offline Actions lab artifact is research-only, not release-ready |
| Checksums | PARTIAL | research artifact has a verified SHA; runtime preview artifact not yet frozen |
| Minimal quickstart | PARTIAL | runtime README documents WSLg path; final downloadable artifact still absent |
| Supported OS/backend | PARTIAL | WSLg/Linux-X11 path documented; acceptance execution still needed |
| Smoke/self-check | PARTIAL | first-run static gate exists; real `doctor` on claimed host remains open |
| Benchmark reconstruction | UNKNOWN for release artifact | full checkout may contain evidence, but offline lab source bundle fails `audit-retained` |
| Fresh golden workflow | OPEN | requires separately authorized supported-host run with independent audit |

## H / T / D / C / U

**H.** The current preview is not yet release-ready solely because launch packaging/acceptance boundaries remain unclosed; the launcher permission defect itself is repairable without runtime-semantic changes.

**T.** Independently reproduce the launcher boundary, verify the packaged offline research artifact digest and contents, attempt the no-GUI `audit-retained` command, and compare the documented supported-host contract with the actual audit environment.

**D.** PASS the launcher repair. FAIL the proposition that `offline-container-lab-9e6d5ecd` is sufficient as a runtime-preview artifact. Keep supported-host real setup/doctor and fresh golden workflow as OPEN/UNKNOWN rather than inferring success.

**C.** A full checkout on the intended WSLg host may pass `audit-retained` and real setup; the offline artifact failure is attributable to its intentionally reduced source content, not necessarily runtime defects.

**U.** No WSLg supported-host execution occurred in this lane. Network/package-index availability, exact Python version on the target host, Windows Codex bridge configuration, Chrome presence, and a fresh model-backed golden run remain the dominant release uncertainties.

## Next release-critical action

On the exact host intended for the 2026-09-17 Research Preview:

1. start from a fresh checkout at a frozen release-candidate SHA;
2. run `python3 release/first_run_smoke_v1/preflight.py --root .`;
3. run `./runtime/setup-golden-demo-v3.sh` and retain the complete real pip/doctor result;
4. run `./runtime/golden-demo-v3.sh audit-retained`;
5. if both pass, execute one fresh persistent-only golden workflow under a new no-retry allocation and immediately run `audit-live`;
6. package that exact checked-out candidate as the downloadable runtime-preview artifact with SHA-256 and explicit WSLg support/limitations.

A failure at any step is release evidence and must be retained; do not substitute the offline research bundle or test-double launcher result for this acceptance boundary.
