# WSLc current-main Fake X experiment series (2026-10-24)

This series checks whether the current-main public guarded-X11 Fake X characterization is portable under the official WSLc API and Python 3.12. It is a synthetic memory-only test: no X server, physical input, desktop, application, MAP01, or live allocation is touched. Each WSLc attempt has a fresh session/container/storage name, a digest-pinned Python image, no container network, read-only source/dependency mounts, saved raw logs, and a no-retry rule. No global WSLc inventory or Docker was used.

| Attempt | Outcome | Finding |
| --- | --- | --- |
| S05 | HOLD before session | WSLc native initialization failed with Win32 error 206 using a 252-character DLL path. |
| S06 | HOLD, no probe result | Short path started WSLc, but the container exited with no captured output. |
| S07 | HOLD, no probe result | Captured `ModuleNotFoundError: Xlib`; runner had not added `/deps` to its own `sys.path`. |
| S08 | HOLD, no case result | Xlib import worked; runtime import required Pillow, absent from the dependency bundle. |
| S09 | HOLD, no case result | All dependency hashes and imports passed; the Fake X owner fixture omitted `_prearm_key_press`. |
| S10 | PASS_PORTABILITY_SCOPED | Local preflight and WSLc normal/optimized reports passed. Each audit passed 26 checks and rejected four mutations. |
| S11 | PASS_PORTABILITY_SCOPED | Independent fresh-session replication of S10; normal/optimized each passed 26 checks and four mutation controls. |

Each attempt retains its own preparation, frozen source/dependency records, WSLc stdout/stderr and lifecycle receipts, result, cleanup record, and `SHA256SUMS.final`. The S05–S09 outcomes remain HOLD; they are not overwritten by S10/S11.

S10 and S11 use baseline `2166707229958e095d472c80e160c26449de7a29`, 247-file source freezes, 203 byte-verified dependencies, and a PyPI-digest-matched Pillow 11.3.0 CPython 3.12 manylinux x86-64 wheel. Under WSLc Python 3.12.14, the `healthy`, `focus_query`, and `release_sync` Fake X cases completed in both normal and optimized modes. Each run's auditor checked 26 conditions and rejected four mutation controls. The checks include public dispatch, simulated key-state neutrality, worker termination, named blocked boundaries, and no late press. Exact container/image/session cleanup succeeded, and the unique VHDX hash/removal is recorded for each attempt.

## Evidence limit and next boundary

S10/S11 support only portability and behavior of the emulated public Fake X path. They do not prove physical input release, real-X behavior, cancellation, bounded recovery of an actual input device, application effects, MAP01 success, efficiency, reliability, or end-to-end computer-control efficacy. A broader claim requires a separately authorized isolated live-X/application environment, exact allocation, instrumented release, and independently verified task effect. Fake X results cannot substitute for that evidence.
