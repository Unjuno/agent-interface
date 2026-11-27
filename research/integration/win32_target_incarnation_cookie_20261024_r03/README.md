# Win32 target-incarnation cookie R03

R03 is a one-shot native Win32 lifecycle check of the production
`Win32Backend.target_generation()` and `close()` methods. On Windows 10 build
26300 with CPython 3.11.9 x64, it created one hidden `STATIC` HWND owned by the
probe process. It did not activate a window, send input, or target an existing
user window.

The native property was present after the first generation query. Two
consecutive generation reads matched. `close()` returned `status=closed` and
`property_cleanup=removed`; a native `GetPropW` read then returned zero. A
generation query after close failed with `target generation unavailable after
backend close`. Finally, `DestroyWindow` succeeded and `IsWindow` returned
false. The result qualifies native property set/read/remove and cleanup
reporting for one same-integrity HWND. It does not test numeric HWND reuse,
cross-integrity/UIPI denial, an atomic check/use fence, user input, release,
task effects, bounded recovery, MAP01, WSLc, efficiency, or reliability.

The immutable raw receipt is [raw.json](raw.json), SHA-256
`cf199d39527cdbbc0ffb3caa688509c064e695b37329f532b6ef403f945c0e6b`.
The one-shot driver is [probe.py](probe.py). R01 and R02 setup failures are
preserved in their own packets; they are not retried.

The local composed regression run passed 79 tests in 18.709 seconds normally
and 79 in 18.911 seconds under `python -O`. It covered
the Win32 property lifecycle, public target-generation admission, Win32 MCP
composition, and session close receipts. Complete raw command output is
retained in [normal mode](raw-local-tests-normal.txt), SHA-256
`1044e829339085de6d0ea0153d1896bf91e5fdf07c963e6ab10e472635656909`, and
[optimized mode](raw-local-tests-optimized.txt), SHA-256
`41318f934887280b6b67676a8ecf8082fbc325edab460d54a98978ad179e0595`.
After removing a test-only dependency between fixtures, the same 79 tests were
rerun: normal mode passed in 18.714 seconds and optimized mode passed in 28.615
seconds. Those raw logs are retained as
[normal recheck](raw-local-tests-recheck-normal.txt), SHA-256
`ac052be32e1f3330bf3c1b4c582ad8ca2432d8930af603635c08c43317f41028`, and
[optimized recheck](raw-local-tests-recheck-optimized.txt), SHA-256
`b3ae8696d982d6fa0ac2a516da8c04eeaa784cffbda26620254db3180790d927`.
The run used the working tree based on `257d1d31c6614dc922057f1c83d49ea81c12b762`;
it is not a WSLc allocation or provider experiment.

Production source snapshots used by this run:

- `runtime/backends/win32_v1/backend.py`: SHA-256
  `869e853258e1d693ec94f82faea1c6152d09203085c83af719894683b8feb63d`
- `runtime/cli_v1/mcp_session.py`: SHA-256
  `ce71063ab94884fc0eacc1056aab5e66163d5cacb300bcfd235f0a351f37f32f`

R03 driver SHA-256: `2b5833ef46914b38e501d4057eec421b8fa173a8bfd2f8f2de14efa9f654d3b6`.

R03 records the earlier design that removed the property at backend close.
That behavior was replaced after reviewing concurrent backend instances:
Win32 does not provide an atomic compare-and-remove operation for window
properties. The current design keeps the shared cookie until Windows destroys
the HWND. The later [R04 packet](../win32_target_incarnation_cookie_20261024_r04/README.md)
validates two backends sharing that property and OS cleanup at HWND destruction.
