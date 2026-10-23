# Win32 target-incarnation cookie R04

R04 is a one-shot no-input native Win32 test of shared marker lifetime. It ran
on Windows 10 build 26300 with CPython 3.11.9 x64 and created one hidden
`STATIC` HWND owned by the probe process. It did not activate a window, send
input, or target an existing user window.

Two independent production `Win32Backend` instances read the same generation
for that HWND. Closing the first backend retained the marker, and the second
backend continued to read the same generation. Closing both retained the
marker until `DestroyWindow`; afterward native `GetPropW` returned zero and
`IsWindow` returned false. Both close reports said
`retained_until_window_destroyed`. This validates the chosen shared-property
lifetime and close behavior for one same-integrity HWND. It does not test
numeric HWND reuse, cross-integrity/UIPI denial, races with destruction,
atomic target check/use, input or release, task effects, bounded recovery,
MAP01, WSLc, efficiency, or reliability.

The immutable [raw receipt](raw.json) has SHA-256
`87f7dc2fb8f8ac3d4f73e9b12860e8657426a54d285f554b12ccbe88492c6a14`.
The one-shot driver is [probe.py](probe.py). Do not rerun R04.

The final local composed suite passed 79 tests normally in 19.458 seconds and
79 tests under `python -O` in 25.888 seconds. It covered the backend marker
lifecycle, standard target-generation admission, Win32 public MCP composition,
and session close handling. Full outputs are retained in [normal mode](raw-local-tests-normal.txt)
and [optimized mode](raw-local-tests-optimized.txt).

Evidence hashes:

- `runtime/backends/win32_v1/backend.py`: `7d936a1cff39b38ec695eb97c90c706f38c91b650faa9adf3c6950270a5334e0`
- `runtime/cli_v1/mcp_session.py`: `ce71063ab94884fc0eacc1056aab5e66163d5cacb300bcfd235f0a351f37f32f`
- `runtime/backends/win32_v1/test_process_identity.py`: `f387e5839724a61f9f9d6b15b9aa2b118ce44ffc4a59ba5fb22ae06527823dde`
- `runtime/cli_v1/test_mcp_session.py`: `2376acf7fc179bb897d5d265756ed1ec73499e6d92b745921936a6625999be6c`
- `runtime/cli_v1/test_owned_win32_session.py`: `70f157dd187ced7a01c9531adf52fdaaec67e68af6cfe1cf677f1b0149f2b7c4`
- `probe.py`: `a651d4722fe685e2d122d46806953d3909a39082060f5f988e9da19f1fdbaa2d`
- `raw-local-tests-normal.txt`: `84c96f193f69bedefb33237751e4ebd4124d854902b7409655823edb50bfdf5b`
- `raw-local-tests-optimized.txt`: `1e36678e59c032be54255003aea708cf361eccbdd8c8f787d56503304f279047`

R03 previously tested property removal on close. That result remains preserved
as historical evidence for the earlier lifecycle design; R04 and the current
implementation supersede it because deleting a shared HWND property is not an
atomic compare-and-remove operation.
