# Standard-caller target-generation Fake X regression

**Run ID:** `AI-TARGET-GENERATION-REGRESSION-20261022-R01`
**Classification:** local Fake X regression; not a formal live experiment
**Test source:** `c5fd95f38d1e4a780ea0c934da7103dafc3b5e8a`
**Base main:** `72ef0303f9ea19406e88b4a00ad1678addf04e05`
**Host/runtime:** Windows, CPython 3.11.9

## Result

Five standard-caller regression cases passed in normal Python and five passed
under `python -O` (10/10). The cases cover refusal after the process-generation
hash changes, stopping a compiled action when process generation changes,
refusal after same-process window destruction/reuse, refusal when destruction
occurs during initial capture, and release of a pressed prefix when a
destroy-notify race occurs between the final local check and XTEST emission.

The first three stale/captured-target cases preserve refusal or avoid a
`TASK_SUCCEEDED` receipt and keep task success null/replay disabled. The
destroy-gap case is an adversarial schedule: a prefix press can occur after the
final local check; the caller then fails, releases the prefix, verifies local
release state, and rejects retry on the retired target. This test exposes a
bounded race rather than proving atomic capture-to-press continuity.

## Evidence and limits

- [`normal.log`](normal.log) and [`optimized.log`](optimized.log) preserve the
  full test output.
- [`CONDITIONS.json`](CONDITIONS.json) records the run order, exact tests,
  interpreter, source and exclusions.
- [`SOURCE_BLOBS.txt`](SOURCE_BLOBS.txt) records the Git blob IDs of the test
  and implementation files used for this check.
- [`SHA256SUMS`](SHA256SUMS) hashes the packet files.

No WSLc, Docker, live X server, physical input, supported application, or MAP01
was used. This is offline caller-construction evidence only. It does not
establish independent task success, bounded live release under blocked platform
I/O, efficiency, or reliability. No formal allocation was consumed.
