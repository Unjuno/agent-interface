# Issue #2907 — public MCP Calc modal-effect construction01

## Disposition

`STOP_CONSTRUCTION_EXCEPTION_NO_RETRY`. The one fresh local Docker invocation did not establish a Calc main-window identity within its bounded 45-second readiness gate. Four visible X windows were found, but the candidate Calc/splash windows lacked `_NET_WM_PID`, `WM_CLASS`, and a useful `WM_NAME`; no owned main Calc root could be selected. The run stopped before starting the public MCP client/server, before any MCP call, and before any GUI input. No dialog effect, binding transition, stale dispatch, or application result was tested.

This is a setup STOP under #2907, not scientific PASS/FAIL of the public MCP action path. It is not retried or pooled. Cleanup left no X socket or visible windows; the launched app/WM launchers were observed in zombie state under PID 1. Full details are in `run-output/construction01/{result.json,trace.partial.json,environment.json,post-cleanup.json,CONTAINER_EXECUTION.json}`.

## Preflight and audit lineage

Three separate display-free, network-disabled Docker preflights are retained. STOP01 attempted to create `/opt/importroot` in the read-only image filesystem and made no MCP call. FAIL02 rejected three `static_valid=true` responses because validation omits `input_dispatched`; the harness expectation was wrong and no display/input existed. Preflight v2 then passed the final frozen runner: Ctrl+O, ESC, and F6 all returned `static_valid=true`, `backend_checked=false`, `runtime_admission=not_evaluated`; no display or input was opened. Raw v2 output is `PREFLIGHT_PASS03.json`.

Independent audit attempt01 stopped before validation because the output directory path collided with its bind mount (`FileExistsError`, `run-output/AUDIT_STOP01.json`). Read-only evidence was unchanged. A second fresh `--network none --read-only` Docker container ran the same frozen `auditor.py` bytes, with the output placed in an absent child directory. It returned `PASS_RAW_AUDIT`, `errors=[]`, while retaining the experiment's `STOP_CONSTRUCTION_EXCEPTION_NO_RETRY` as the scientific disposition. Audit JSON: `run-output/audit01/audit02/AUDIT.json`.

## H/T/D/C/U

- **H:** One public persistent-X11 MCP session can open a Calc native Open dialog through MCP input, independently verify its appearance/disappearance, rebind dialog and original root, and reject two stale binding revisions before backend emissions.
- **T:** Frozen in `FREEZE.md`. Exactly one fresh Docker invocation was made; it stopped at Calc identity readiness before public MCP initialization. No retry.
- **D:** Effect-scope PASS requires the full frozen call sequence, X11 effect oracle, both stale refusals/zero emissions, two neutral dispatches, return-to-root review, close/release and retained readbacks. The readiness prerequisite was not met; final outcome is `STOP_CONSTRUCTION_EXCEPTION_NO_RETRY`, not a PASS.
- **C:** Image `public-mcp-three-app-2907:formal01`, ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, Linux/amd64; root and source readonly, network none, 512 PIDs/4 GiB/2 CPUs; one local Calc/Xvfb attempt and separate offline read-only audit. Relevant source Git blobs match the intake main reference recorded in the freeze; the inherited full source closure is explicitly not claimed as that main snapshot.
- **U:** No MCP operation or app effect was exercised; no public-session/lease/controller behavior was tested, and the full mixed-app four-transition #2907 acceptance, #2789 six-task matched integration, task/model benefit, or runtime/product readiness remain open.

## Source and reproducibility

Runner SHA-256: `b303f930d04f3f488337da609ec2cba2b84f6816b7d9df5f902c19d524ed17d6`. Auditor SHA-256: `b3361cf1e40556f775dd9634783b9098194d057675cc916bb097bf060f61648c`. Source/main identity and seven verified runtime blob IDs are in `FREEZE.md`; exact local Docker image ID and resource envelope are in `run-output/construction01/CONTAINER_EXECUTION.json`. The image mount was `--pull=never --network none --read-only`, with only `/tmp`, `/opt/importroot`, and the dedicated output mount writable. The run output hashes include:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `environment.json` | 1,035 | `175eb16e145d2ba9422153549699f110f5fec9bac3dbe424b27901195ca97fba` |
| `post-cleanup.json` | 223 | `2823cbadcd41af88d5f18c11a87988b14af4212978821d5c79d9ad0bc481d041` |
| `result.json` | 3,309 | `358dce134ced59eb4327596e5fde97b0afa5da4017f2f6a7c9542f89303945de` |
| `trace.partial.json` | 1,652 | `ed32344392d746e47ea8100709beda61d9b79ce55ff889914f34d421fcef9277` |
| read-only raw audit | 628 | `edbe4e0ca7d6eba3dbb9fdd0616d53dbeba106d10484d42909c7c08229ef5f30` |

No GitHub Actions/workflow was dispatched. Issue #2907 and spine issue #2789 remain open. This construction STOP is recorded under the existing issue, not split into a new research issue.
