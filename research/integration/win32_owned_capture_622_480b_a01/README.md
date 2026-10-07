# Owned invisible Win32 capture, first allocation A01

Scientific result: FAIL_SCOPED_NATIVE_PIXEL_CROP. This archive preserves the first result; it does not repair or replay the native experiment.

Parent: https://github.com/Unjuno/agent-interface/issues/622
Prospective freeze: https://github.com/Unjuno/agent-interface/issues/622#issuecomment-5970106854
Full original public packet: https://github.com/Unjuno/agent-interface/issues/622#issuecomment-5970155078
Public DATA-only readback: https://github.com/Unjuno/agent-interface/issues/622#issuecomment-5970283373

H: the literal Win32 backend captures a known four-color 16x16 raster from an owned invisible HWND and projects correct crop bytes/hashes. T: one frozen native allocation, four positive capture regions and two invalid dimensions/bounds. D: the prospective raster, projection, negative, owner and cleanup checks must all hold. C/U: same-thread hidden fixture rendering is a prerequisite; no event pump or visible application was exercised. No population, mixed-DPI, arbitrary-app support, input release, latency or task-effect claim.

Literal source base 5feefbcafc1d5f907774462660a019f4172b0d16. Backend blob e90a08b35c040038cee3de755c1b365e4f0f5f47 and core contract blob 231ab75625e7d88bbf440b90d7e15cb64cd13f44 were exported before execution. Empty package bridges are local harness files, not repository provenance. FREEZE.json retains the exact protocol and runner/launcher/source pins.

Actual native child27672 ran 2026-10-03T14:30:58.827361+00:00 to14:30:58.946357+00:00, exit0, watchdog timeout false. All four positive calls returned 1024 black BGRA bytes, PrintWindow returned nonzero, and no WM_PRINT/WM_PRINTCLIENT callbacks were recorded. The six rows and full buffers are in RAW.json. Invalid bounds/dimensions were refused before capture allocation. Own HWND, four brushes and class cleanup all returned true; no input, focus, screen capture or other-app handles were used.

Separate first saved-data reader3028 exited1: missing four rendering callbacks plus1024 coordinate pixel mismatches. Crop/hash/length projections of the actual black buffers, typed negative cases, source pins, call counts and cleanup joined. AUDIT.json preserves all1025 first errors. These observations establish failure of the frozen known-raster test, not a proven defect in crop indexing or a cause for the absent rendering stimulus. API success and a correctly shaped SHA256 alone did not establish the expected pixels.

The complete26-member public packet was decoded as DATA and matched every original byte, length and hash by actual child30564 exit0. The first publication reader31536 exit1 used an incorrect local source alias; it was preserved, then explicit alias mapping corrected without executing decoded source or rerunning native capture. Publication integrity success does not change science FAIL.

All Python images in this archive have .py.txt suffixes, including empty bridge files. No executable tests, package initializers, runtime edits or workflow edits are supplied. CUSTODY.json binds each public packet member to its inert archive path and original bytes. SHA256SUMS covers every archive file except itself. Review must still inspect current discovery/import/config context before any main integration; local packaging is not approval.

Future investigation requires a materially distinct, prospectively fixed fixture calibration or message-delivery protocol and fresh allocation. A new ID alone does not authorize replay of A01. All original failures remain.
