# T7 formal disposition — `STOP_AUDIT_MISMATCH`

- Allocation: `gluing-approx-irreversible-5537-t7-20261001-01`.
- Freeze base: `3befc5fb720e8d8aed3f6e6f3e6e881c42070f8e`; runtime CPython 3.14.5/macOS arm64; host-local, no container or external effect.
- Construction tests: 3/3 pass; py_compile pass.
- Runner: one `python3 -B run_experiment.py`, exit 0, 135 rows; raw SHA-256 `fd842027179dcb25306e38d54176ad9d4b4e86e43197da28631c07e294561732`.
- Auditor: one `python3 -B audit_raw.py`, exit 1, base errors `[]`, but only 5/6 preregistered mutation controls rejected; audit receipt SHA-256 `8791d84ec30f22f2f4b97bd7fd37c168e75b309e6f9ec059b721de18a546b0eb`.
- The specifically selected false-admission mutation targeted one row whose base decision was `admitted=false`, and was rejected.
- Read-only diagnosis found the `false_status` control targets row 0, whose exact base status is already `GLOBAL_SECTION_CERTIFIED`; it therefore made no change and was not rejected. No retry or post-freeze edits were made.

The base oracle agrees on all 135 rows, but the preregistered 6/6 mutation gate failed. No scientific PASS is accepted. Preserve this STOP unchanged. Any further attempt must be a new allocation with a generic before/after mutation non-identity assertion for every control.
