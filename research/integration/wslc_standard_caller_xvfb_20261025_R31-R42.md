# WSLc standard-caller R31–R42 — bounded-release deadline boundary

R37–R41 passed the unchanged standard caller at private-Xvfb pauses of 3,500–3,800 ms, each with old/fresh synthetic task oracles, independent all-up checks, a clear late-event horizon, and runtime cancellation still UNKNOWN/replay-denied/task-success-null. Release margins were 377.305 ms (R37), 272.051 ms (R38), 176.865 ms (R39), 76.372 ms (R40), and 72.300 ms on the independent R41 repeat. R42 at 3,900 ms exceeded the 4 s transaction deadline by 4.988 ms; its public caller assertion failed and cleanup/release status stayed UNKNOWN. Independent release readback and task oracles were not reached for R42. See each linked result and retained raw/audit packet.

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
| [R41](wslc_standard_caller_xvfb_20261025_r41/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3800MS (27/27) | Independent 3.8 s repeat; release margin 72.300 ms; public caller and both synthetic task oracles passed |
| [R42](wslc_standard_caller_xvfb_20261025_r42/RESULT.md) | FAIL_BOUNDARY_TRANSACTION_DEADLINE_UNKNOWN (24/24 evidence checks) | At 3.9 s the transaction finished 4.988 ms after its deadline; release stayed UNKNOWN and the test stopped before independent readback/task oracles |

R31–R36 are setup diagnostics, not control outcomes, and were not replayed. R37–R42 are isolated synthetic Xvfb container trials on the user-authorized PC with the digest-pinned Ubuntu image and no network. Private R31/R32 host identity logs remain local; the published summaries preserve their stop classifications and zero-input dispositions. These results do not establish Win32/MAP01 or real-application transfer, matched efficiency, or broad reliability. R42 does not establish input release; teardown of its synthetic X server is not an agent release receipt.
