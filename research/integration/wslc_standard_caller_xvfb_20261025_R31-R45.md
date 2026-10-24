# WSLc standard-caller R31–R45 — bounded-release transaction boundary

R31–R36 stopped before input while resolving the private-Xvfb/container setup. R37–R41 passed the unchanged public standard caller at 3,500–3,800 ms pauses, with supervisor release/readback margins from 377.305 down to 72.300 ms; each reached independent all-up checks, the late-event horizon, and both synthetic task oracles. R42 at 3,900 ms exceeded the 4 s transaction deadline by 4.988 ms and remained UNKNOWN. After that boundary, R43 passed at 3,850 ms with 27.552 ms margin, R44 failed at 3,875 ms by 0.466 ms, and R45 passed at 3,860 ms with 20.877 ms margin. The narrow R43–R45 transition shows timing variability near the deadline and does not support a reliability estimate.

| Attempt | Disposition | Input/test-body status |
|---|---|---|
| [R31](wslc_standard_caller_xvfb_20261025_r31/RESULT.md) | STOP_PREINPUT: Xvfb rejected `/tmp/.X11-unix` mode 0777 without sticky bit | Caller not started; zero input |
| [R32](wsl_local_xvfb_20261025_r32/RESULT.md) | STOP_PREINPUT: WSLg mounts the X socket directory read-only | Caller not started; zero input |
| [R33](wslc_standard_caller_xvfb_20261025_r33/RESULT.md) | STOP_PRECONTAINER: Docker Desktop could not access the WSL UNC XKB source | No container created; zero input |
| [R34](wslc_standard_caller_xvfb_20261025_r34/RESULT.md) | STOP_PREINPUT: staged Python lacked initial `PYTHONHOME`/`LD_LIBRARY_PATH` | Runner and Xvfb not started; zero input |
| [R35](wslc_standard_caller_xvfb_20261025_r35/RESULT.md) | STOP_PREINPUT: private `/tmp` tmpfs was `noexec` | Runner and Xvfb not started; zero input |
| [R36](wslc_standard_caller_xvfb_20261025_r36/RESULT.md) | STOP_PREINPUT: CRLF added a trailing carriage return to the runner path | Runner and Xvfb not started; zero input |
| [R37](wslc_standard_caller_xvfb_20261025_r37/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3500MS (26/26) | Release margin 377.305 ms; public caller and both synthetic task oracles passed |
| [R38](wslc_standard_caller_xvfb_20261025_r38/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3600MS (27/27) | Release margin 272.051 ms; public caller and both synthetic task oracles passed |
| [R39](wslc_standard_caller_xvfb_20261025_r39/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3700MS (27/27) | Release margin 176.865 ms; public caller and both synthetic task oracles passed |
| [R40](wslc_standard_caller_xvfb_20261025_r40/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3800MS (27/27) | Release margin 76.372 ms; public caller and both synthetic task oracles passed |
| [R41](wslc_standard_caller_xvfb_20261025_r41/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3800MS (27/27) | Independent repeat; release margin 72.300 ms; both task oracles passed |
| [R42](wslc_standard_caller_xvfb_20261025_r42/RESULT.md) | FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN (24/24) | At 3,900 ms transaction completed 4.988 ms late; no independent readback/task oracle |
| [R43](wslc_standard_caller_xvfb_20261025_r43/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3850MS (26/26) | Release margin 27.552 ms; independent readback and both task oracles passed |
| [R44](wslc_standard_caller_xvfb_20261025_r44/RESULT.md) | FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN (24/24) | At 3,875 ms transaction exceeded deadline by 0.466 ms; release remained UNKNOWN |
| [R45](wslc_standard_caller_xvfb_20261025_r45/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3860MS (26/26) | Release margin 20.877 ms; independent readback and both task oracles passed |

R43–R45 used distinct pre-registered attempt IDs, the same pinned source commit `e4e34a163e1f288d8841d300ae719abcf9e58223`, digest-pinned Ubuntu, network-disabled containers, and isolated outputs. Each exact container and Xvfb process was removed. Raw outputs and per-attempt audits are retained beside each result. Supervisor release receipts are separate from runtime cancellation custody: for all passes runtime custody remains UNKNOWN, `release_confirmed=false`, replay denied, and `task_success=null`. Failure cases stop before independent release readback and task oracles; teardown is not evidence of input release.

These are synthetic-Xvfb standard-caller results on the user-authorized PC only. They do not establish Win32 desktop or MAP01 behavior, real-application task transfer, model/provider use, matched efficiency, or broad reliability. The next discriminating work should move to an independently justified boundary condition or a real supported-app effect path; do not repeat a consumed allocation or claim a safe timeout threshold from these samples alone.
