# Issue #7387 T0 A02 — fresh candidate after A01 STOP

Successor allocation `SERIAL-CUE-7387-T0-WSLC-A02-20261004`; A01's terminal output-directory STOP and source remain immutable. The scientific/method gate is unchanged; A02 changes only the candidate's mount-root contract: accept an existing empty `/out` directory and reject a nonempty one. A02 has its own candidate, tests, freeze, output path and one-shot invocation boundary.

The design and independent pixel auditor are reused byte-for-byte from the frozen A01 package at `../serial_cue_interference_7387_t0_20261004/`. Their A01 source hashes are retained there. A02 tests that the new candidate still satisfies that oracle, including a populated-output refusal control. This reuse does not count A01's candidate run as A02 data; A01 emitted zero rows.

Construction history: the first A02 unittest attempt imported A01's same-named `candidate` module due Python path precedence; the clean-empty-root test therefore reproduced A01's STOP. The test now imports the A02 file by explicit path and the three construction tests pass. No A02 formal invocation occurred during construction.

T0 remains no-model construction only: 144 matched cue sequences, 288 presentations, 16 isolated controls and 1,280 small PPM image files. The files contain five distinct pixel payloads (one blank frame and four glyphs); file/path count is not stimulus-image diversity. No serial-interference/model hypothesis is tested.
