# WSLc standard-caller R31–R38 — setup stops and 3.5–3.6 s boundary results

R37 and R38 reached the unchanged public standard-caller test at 3,500 and 3,600 ms private-Xvfb pauses under the 4 s cancellation transaction deadline. R37 passed 26/26 audit checks with 377.305 ms of release margin; R38 passed 27/27 with 272.051 ms. Independent parent readback and each +8.5 s horizon saw all keys up, with no delayed `b`; old and fresh synthetic task oracles passed. Runtime cancellation remained UNKNOWN, replay denied, and runtime task success null. See the [R37 result](wslc_standard_caller_xvfb_20261025_r37/RESULT.md) and [R38 result](wslc_standard_caller_xvfb_20261025_r38/RESULT.md), with their retained conditions, raw output, audits and cleanup receipts.

| Attempt | Disposition | Input/test-body status |
|---|---|---|
| [R31](wslc_standard_caller_xvfb_20261025_r31/RESULT.md) | STOP_PREINPUT: Xvfb rejected `/tmp/.X11-unix` mode 0777 without sticky bit | Caller not started; zero input |
| [R32](wsl_local_xvfb_20261025_r32/RESULT.md) | STOP_PREINPUT: WSLg mounts the X socket directory read-only | Caller not started; zero input |
| [R33](wslc_standard_caller_xvfb_20261025_r33/RESULT.md) | STOP_PRECONTAINER: Docker Desktop could not access the WSL UNC XKB source | No container created; zero input |
| [R34](wslc_standard_caller_xvfb_20261025_r34/RESULT.md) | STOP_PREINPUT: staged Python lacked initial `PYTHONHOME`/`LD_LIBRARY_PATH` | Runner and Xvfb not started; zero input |
| [R35](wslc_standard_caller_xvfb_20261025_r35/RESULT.md) | STOP_PREINPUT: private `/tmp` tmpfs was `noexec` | Runner and Xvfb not started; zero input |
| [R36](wslc_standard_caller_xvfb_20261025_r36/RESULT.md) | STOP_PREINPUT: CRLF added a trailing carriage return to the runner path | Runner and Xvfb not started; zero input |
| [R37](wslc_standard_caller_xvfb_20261025_r37/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3500MS (26/26) | One public-caller synthetic-Xvfb run; exact container removed |
| [R38](wslc_standard_caller_xvfb_20261025_r38/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3600MS (27/27) | One fresh 3.6 s standard-caller sample; release margin 272.051 ms; all-up at +3.884 s and +8.504 s; no delayed `b`; old/fresh task oracles passed; runtime UNKNOWN preserved |

R31–R36 are setup diagnostics, not control outcomes, and were not replayed. R38 repeated the current-main standard caller at 3,600 ms: the 27/27 audit passed with a 272.051 ms release margin. Its initial audit false negative and corrected audit are both retained. Private R31/R32 host identity logs remain local; the published results preserve the failure classes and zero-input disposition. These results are containerized synthetic Xvfb only; they do not establish Win32/MAP01 or real-application transfer, matched efficiency, or general reliability.
