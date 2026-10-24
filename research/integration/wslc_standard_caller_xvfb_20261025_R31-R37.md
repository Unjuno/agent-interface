# WSLc standard-caller R31–R37 — setup stops and 3.5 s boundary result

R37 is the first run in this continuation to reach the standard-caller test. It passes all 26 independent audit checks at a 3,500 ms private-Xvfb pause under the 4 s cancellation transaction deadline. Supervisor release/readback completed with 377.305 ms remaining; independent parent readback at +3,752.893 ms and the +8,504.193 ms horizon both saw all keys up, with no delayed `b`. Old and fresh synthetic task oracles passed. Runtime cancellation remains UNKNOWN, replay denied, and runtime task success null. See the [R37 result](wslc_standard_caller_xvfb_20261025_r37/RESULT.md) and its retained conditions, raw caller result, audit and cleanup receipts.

| Attempt | Disposition | Input/test-body status |
|---|---|---|
| [R31](wslc_standard_caller_xvfb_20261025_r31/RESULT.md) | STOP_PREINPUT: Xvfb rejected `/tmp/.X11-unix` mode 0777 without sticky bit | Caller not started; zero input |
| [R32](wsl_local_xvfb_20261025_r32/RESULT.md) | STOP_PREINPUT: WSLg mounts the X socket directory read-only | Caller not started; zero input |
| [R33](wslc_standard_caller_xvfb_20261025_r33/RESULT.md) | STOP_PRECONTAINER: Docker Desktop could not access the WSL UNC XKB source | No container created; zero input |
| [R34](wslc_standard_caller_xvfb_20261025_r34/RESULT.md) | STOP_PREINPUT: staged Python lacked initial `PYTHONHOME`/`LD_LIBRARY_PATH` | Runner and Xvfb not started; zero input |
| [R35](wslc_standard_caller_xvfb_20261025_r35/RESULT.md) | STOP_PREINPUT: private `/tmp` tmpfs was `noexec` | Runner and Xvfb not started; zero input |
| [R36](wslc_standard_caller_xvfb_20261025_r36/RESULT.md) | STOP_PREINPUT: CRLF added a trailing carriage return to the runner path | Runner and Xvfb not started; zero input |
| [R37](wslc_standard_caller_xvfb_20261025_r37/RESULT.md) | PASS_SCOPED_4S_TRANSACTION_3500MS (26/26) | One public-caller synthetic-Xvfb run; exact container removed |

R31–R36 are setup diagnostics, not control outcomes, and were not replayed. The complete unredacted local raw packets remain in the working directory. These results are containerized synthetic Xvfb only; they do not establish Win32/MAP01 or real-application transfer, matched efficiency, or general reliability.
