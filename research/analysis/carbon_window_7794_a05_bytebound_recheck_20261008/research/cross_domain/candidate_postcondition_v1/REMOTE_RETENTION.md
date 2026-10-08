# Retrospective GitHub retention boundary

This directory publishes evidence from `CANDIDATE-POSTCONDITION-20260916-001` after the experiment completed.

It is **not** a remote preregistration. At measurement time, GitHub read operations worked but the connector returned `Resource not found` for write actions. The measured code and plan were instead frozen locally before scored execution:

- original recorded publication base: `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`
- local premeasurement freeze commit: `b178331f1e3348a6aea538441b6030ed5a256695`
- byte-exact plan SHA-256: `8d6777275018361c9004eeea29902e2cf1b4d0d89a2bd29246b3ef3ac588587b`
- evidence archive SHA-256: `96674054f2042e257e8d88053ab8fed40077a056311e405ca9a0c959a750a990`
- full user ZIP SHA-256: `c712d1eca7fb3aceb60a6402f76a035cbb091a51cbae4bb51bccc5365556d753`

GitHub write access became available later. Issue #364 and branch `research/candidate-postcondition-0a6012d` therefore retain the already-completed result without changing the original allocation, source hashes, plan, measured IDs, or first outcomes.

The historical `REPORT.md` and `VALIDATION.json` intentionally preserve their original statement that remote reflection was unavailable at execution time. This note records the later publication event rather than rewriting those historical artifacts.

GitHub contains exact executable source, the byte-exact frozen plan, the compact 72-row verdict table, report, validation summary, and environment metadata. Full retained native repositories/process transcripts remain conversation artifacts rather than being uploaded here.
