# Session-bound producer → scorer → input-envelope composition (Issue #59)

This successor updates T0 to the current source snapshots: the sampler now
retains external update acknowledgments and poisons itself after failures
(draft #7545), and the occurrence reducer now requires one shared `session_id`
and reports only `SINGLE_POSSIBLE_INTENT_ENVELOPE` (draft #7546). T0's
`unique_temporal_occurrence` result is preserved as historical evidence for its
older frozen API; it is not the current interpretation.

The deterministic construction feeds the current `AcknowledgedSampler` with a
fake game, converts two samples into a positive event through current-main
`ProgressClock`, and composes that event with the current session-bound
occurrence-envelope reducer. Producer `run_id` is copied to scorer samples and
events as their `session_id`; the reducer then accepts action records only when
they already carry that same session ID. The independent audit verifies one
possible envelope for `owner-a:1`, the producer `session-A/sample-2/update-2`,
cross-session rejection, and an unresolved sample exactly at the release-sync
return boundary. No unique active key or causal effect is claimed.
Test timestamps are deterministic integer nanoseconds and tic values are
synthetic engine-tic counts.

Eleven focused tests pass on Windows 11 Pro/Python 3.13 and Ubuntu WSL/Python
3.12. They cover exact update-sidecar/sample equality, explicit and cancellation
release records, terminal-repeat state, external terminal update acknowledgments,
duplicate or missing source identity, and release-endpoint ordering.
`TESTS_v1_failed.txt` retains the first
assertion-text mismatch; the candidate behavior already rejected the duplicate
sequence correctly.

## Remaining source gap

The reducer source requires `session_id` on admission, release, and semantic
binding rows. The current `input_owner_v12.py` snapshot has neither `session_id`
nor `run_id`. This construction supplies the field only in its synthetic
action fixture, so it demonstrates the required fail-closed composition
contract, not actual producer-to-owner runtime wiring. The next source/runtime
step must carry the V16 run identity into those real owner records before a
controlled session can qualify. The hash-bound absence check is retained in
[`SOURCE_FIELD_AUDIT.md`](SOURCE_FIELD_AUDIT.md).

The raw candidate JSON is deterministic across both hosts. Its canonical JSON
SHA-256 is `1f68042baa52b42260b841f6df20ef9da59a3b9f0a4b563f3783e389d9c64b7d`;
the Windows and WSL byte hashes differ only by CRLF versus LF. The 25-file
source/result manifest passes its separate hash audit.

No ViZDoom engine, actual V16 session, X11 server, model, GPU, game allocation,
physical input, task effect, or recovery test ran. The Windows raw path was
overwritten by the planned WSL run; a CRLF reconstruction matches the recorded
Windows raw hash, and `CROSS_PLATFORM_AUDIT.json` confirms parsed equality. WSLc
is unavailable; this CPU-only construction used native Windows Python and the
installed Ubuntu WSL distro.
