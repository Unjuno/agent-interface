# Win32 guarded-input boundary audit — R01

Date: 2026-10-22. Source: current main `609669715c95d6c3bebc338d43940054fcdc1796`.

## Question

Does the existing Win32 input path provide independent, bounded recovery when a native operation is blocked?

## Source findings

- `runtime/backends/win32_v1/Win32RuntimeSession.dispatch()` calls `backend.execute()` synchronously. `recover_input()` calls `backend.release_all()` synchronously.
- The backend sends tracked key/button UP events with `SendInput`, waits 10 ms, and samples `GetAsyncKeyState`. A zero/ambiguous state remains unknown; an UP insertion is not treated as application-effect proof.
- The opt-in `runtime/guarded_win32_v1/MoveBridge` holds one nonblocking operation lock through execution and recovery. A concurrent recovery while that lock is held is refused as `OPERATION_ACTIVE`; it does not attempt a second release. The prototype README says native capture/release are not forcibly preemptible and native state can change after the final guard inside emission.
- Therefore this path does not qualify as an independent safety supervisor under blocked Win32 API I/O. Its conservative lock prevents concurrent unsafe release, but it also cannot produce a bounded release until the current operation yields. This audit adds no runtime behavior.

## Local checks

On Windows CPython 3.13.14, against the above source:

- `py -3 -m unittest runtime.backends.win32_v1.test_explicit_up_ledger runtime.backends.win32_v1.test_release_ledger runtime.backends.win32_v1.test_unknown_release_custody`: 22/22 passed.
- `py -3 -O -m unittest runtime.backends.win32_v1.test_explicit_up_ledger runtime.backends.win32_v1.test_release_ledger runtime.backends.win32_v1.test_unknown_release_custody`: 22/22 passed.
- `py -3 -m unittest discover -s runtime/guarded_win32_v1 -p 'test_*.py'`: 31/31 passed.
- `py -3 -O -m unittest discover -s runtime/guarded_win32_v1 -p 'test_*.py'`: 31/31 passed.

These are inert API and composition tests. The guarded tests emitted synthetic child-worker records and synthetic retained images; they did not send real input. The historical hosted Windows Server 2025 fixture run recorded in `runtime/backends/win32_v1/REPORT.md` passed 8/8 and checked one task effect, but did not stall a native API call or exercise concurrent cancellation.

## Result and next discriminator

Decision: **not qualified**. Keep the backend's existing UNKNOWN/quarantine behavior and do not infer release bounds from successful ordinary native use. A future separately reviewed design/test must block a native operation after input admission, request recovery concurrently, record whether release can complete before the operation returns, then verify that the retired producer cannot emit any later DOWN, independently read actual input state, and check a separate fresh target's task effect. A concurrent UP without producer fencing could be followed by a late DOWN and is not an acceptable fix.

No WSLc/Docker allocation or native desktop input was used. The `raw/` directory retains the six test JSON records, four mode-specific test logs, and 402 generated synthetic PNGs. `SHA256SUMS` covers this README and every file in `raw/`.
